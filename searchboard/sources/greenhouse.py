from datetime import date, datetime
import re
import httpx
from searchboard.job import Job, make_id
from searchboard.sources import register
from searchboard.sources.base import Source

_HTML = re.compile(r"<[^>]+>")
_SALARY = re.compile(r"\$(\d{2,3}(?:,\d{3})?)\s*[–-]\s*\$(\d{2,3}(?:,\d{3})?)")


def _strip_html(s: str) -> str:
    return _HTML.sub(" ", s or "").replace("&nbsp;", " ").strip()


def _parse_salary(metadata: list[dict]) -> tuple[int | None, int | None]:
    for m in metadata or []:
        if "salary" in (m.get("name") or "").lower():
            v = str(m.get("value") or "")
            mt = _SALARY.search(v)
            if mt:
                lo = int(mt.group(1).replace(",", ""))
                hi = int(mt.group(2).replace(",", ""))
                return lo, hi
    return None, None


@register("greenhouse")
class Greenhouse(Source):
    URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    def __init__(self, slugs: list[str], timeout: float = 15.0):
        self.slugs = slugs
        self.timeout = timeout
        self.failed_slugs: list[str] = []

    def fetch(self) -> list[Job]:
        out: list[Job] = []
        with httpx.Client(timeout=self.timeout) as c:
            for slug in self.slugs:
                try:
                    r = c.get(self.URL.format(slug=slug), params={"content": "true"})
                except httpx.HTTPError:
                    self.failed_slugs.append(slug)
                    continue
                if r.status_code in (404, 410):
                    self.failed_slugs.append(slug)
                    continue
                if r.status_code != 200:
                    continue
                for j in r.json().get("jobs", []):
                    out.append(self._to_job(slug, j))
        return out

    def _to_job(self, slug: str, j: dict) -> Job:
        posting_id = str(j["id"])
        loc_name = (j.get("location") or {}).get("name") or ""
        remote = "remote" in loc_name.lower()
        lo, hi = _parse_salary(j.get("metadata") or [])
        posted = None
        if upd := j.get("updated_at"):
            try:
                posted = datetime.fromisoformat(upd.replace("Z", "+00:00")).date()
            except ValueError:
                posted = None
        desc = _strip_html(j.get("content", ""))[:3000]
        return Job(
            id=make_id("greenhouse", slug, posting_id),
            source="greenhouse",
            company=slug.replace("-", " ").title(),
            title=j.get("title", ""),
            location=loc_name,
            remote=remote,
            salary_min=lo, salary_max=hi,
            url=j.get("absolute_url", ""),
            posted_at=posted,
            seen_at=date.today(),
            description_text=desc,
        )
