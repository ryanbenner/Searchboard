from datetime import date, datetime, timezone
import re
import httpx
from searchboard.job import Job, make_id
from searchboard.sources import register
from searchboard.sources.base import Source

_SALARY = re.compile(r"\$(\d{2,3}(?:,\d{3})?)\s*[–-]\s*\$(\d{2,3}(?:,\d{3})?)")


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    m = _SALARY.search(text or "")
    if not m:
        return None, None
    return int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))


@register("lever")
class Lever(Source):
    URL = "https://api.lever.co/v0/postings/{slug}"

    def __init__(self, slugs: list[str], timeout: float = 15.0):
        self.slugs = slugs
        self.timeout = timeout
        self.failed_slugs: list[str] = []

    def fetch(self) -> list[Job]:
        out: list[Job] = []
        with httpx.Client(timeout=self.timeout) as c:
            for slug in self.slugs:
                try:
                    r = c.get(self.URL.format(slug=slug), params={"mode": "json"})
                except httpx.HTTPError:
                    self.failed_slugs.append(slug)
                    continue
                if r.status_code in (404, 410):
                    self.failed_slugs.append(slug)
                    continue
                if r.status_code != 200:
                    continue
                for j in r.json():
                    out.append(self._to_job(slug, j))
        return out

    def _to_job(self, slug: str, j: dict) -> Job:
        cats = j.get("categories", {}) or {}
        loc = cats.get("location", "") or ""
        remote = "remote" in loc.lower()
        desc = (j.get("descriptionPlain") or "")[:3000]
        lo, hi = _parse_salary(desc)
        posted = None
        if ts := j.get("createdAt"):
            try:
                posted = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
            except (ValueError, OSError):
                posted = None
        return Job(
            id=make_id("lever", slug, str(j["id"])),
            source="lever",
            company=slug.replace("-", " ").title(),
            title=j.get("text", ""),
            location=loc,
            remote=remote,
            salary_min=lo, salary_max=hi,
            url=j.get("hostedUrl", ""),
            posted_at=posted,
            seen_at=date.today(),
            description_text=desc,
        )
