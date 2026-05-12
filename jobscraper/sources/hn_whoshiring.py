from datetime import date, datetime, timezone
import re
import httpx
from jobscraper.job import Job, make_id
from jobscraper.sources import register
from jobscraper.sources.base import Source
from jobscraper.url_filter import looks_like_job_url


_HTML = re.compile(r"<[^>]+>")


def _strip_html(s: str) -> str:
    return _HTML.sub(" ", s or "").replace("&#x2F;", "/").strip()


@register("hn")
class HNWhosHiring(Source):
    SEARCH = "https://hn.algolia.com/api/v1/search"
    ITEM   = "https://hn.algolia.com/api/v1/items/{sid}"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(self.SEARCH, params={
                "query": "Ask HN Who is hiring",
                "tags": "story",
                "hitsPerPage": 5,
            })
            if r.status_code != 200:
                return []
            hits = r.json().get("hits", [])
            story = next((h for h in hits if "who is hiring" in (h.get("title") or "").lower()), None)
            if not story:
                return []

            sid = story["objectID"]
            r2 = c.get(self.ITEM.format(sid=sid))
            if r2.status_code != 200:
                return []
            thread = r2.json()

        out: list[Job] = []
        for child in thread.get("children", []) or []:
            j = self._to_job(child)
            if j:
                out.append(j)
        return out

    def _to_job(self, c: dict) -> Job | None:
        text = _strip_html(c.get("text") or "")
        if not text or "|" not in text:
            return None
        header = text.split("\n", 1)[0]
        parts = [p.strip() for p in header.split("|")]
        if len(parts) < 2:
            return None
        company = parts[0]
        title = parts[1]
        location = parts[2] if len(parts) > 2 else ""
        remote = "remote" in text.lower()
        posted = None
        if ts := c.get("created_at_i"):
            try:
                posted = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            except (ValueError, OSError):
                posted = None
        url = None
        for m in re.finditer(r"https?://\S+", text):
            candidate = m.group(0).rstrip(").,;\"'<>")
            if looks_like_job_url(candidate):
                url = candidate
                break
        if not url:
            return None
        sm = re.search(r"\$(\d{2,3})k\s*[–-]\s*\$?(\d{2,3})k", text)
        salary_min = int(sm.group(1)) * 1000 if sm else None
        salary_max = int(sm.group(2)) * 1000 if sm else None
        return Job(
            id=make_id("hn", "hn", str(c["id"])),
            source="hn",
            company=company,
            title=title,
            location=location or ("Remote" if remote else ""),
            remote=remote,
            salary_min=salary_min, salary_max=salary_max,
            url=url,
            posted_at=posted,
            seen_at=date.today(),
            description_text=text[:3000],
        )
