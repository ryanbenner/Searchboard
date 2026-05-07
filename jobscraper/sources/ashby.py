from datetime import date, datetime
import re
import httpx
from jobscraper.job import Job, make_id
from jobscraper.sources import register
from jobscraper.sources.base import Source

_SALARY = re.compile(r"\$(\d{2,3}(?:,\d{3})?)\s*[–-]\s*\$(\d{2,3}(?:,\d{3})?)")


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    m = _SALARY.search(text or "")
    if not m:
        return None, None
    return int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))


@register("ashby")
class Ashby(Source):
    URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

    def __init__(self, slugs: list[str], timeout: float = 15.0):
        self.slugs = slugs
        self.timeout = timeout
        self.failed_slugs: list[str] = []

    def fetch(self) -> list[Job]:
        out: list[Job] = []
        with httpx.Client(timeout=self.timeout) as c:
            for slug in self.slugs:
                try:
                    r = c.get(self.URL.format(slug=slug),
                             params={"includeCompensation": "true"})
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
        desc = (j.get("descriptionPlain") or "")[:3000]
        lo, hi = _parse_salary(desc)
        posted = None
        if pub := j.get("publishedAt"):
            try:
                posted = datetime.fromisoformat(pub.replace("Z", "+00:00")).date()
            except ValueError:
                posted = None
        return Job(
            id=make_id("ashby", slug, str(j["id"])),
            source="ashby",
            company=slug.replace("-", " ").title(),
            title=j.get("title", ""),
            location=j.get("locationName") or "",
            remote=bool(j.get("isRemote")),
            salary_min=lo, salary_max=hi,
            url=j.get("jobUrl", ""),
            posted_at=posted,
            seen_at=date.today(),
            description_text=desc,
        )
