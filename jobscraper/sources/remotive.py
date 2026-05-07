from datetime import date, datetime
import re
import httpx
from jobscraper.job import Job, make_id
from jobscraper.sources import register
from jobscraper.sources.base import Source

_HTML = re.compile(r"<[^>]+>")
_SALARY = re.compile(r"\$(\d{2,3}(?:,\d{3})?)\s*[–-]\s*\$(\d{2,3}(?:,\d{3})?)")


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "unknown"


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    m = _SALARY.search(text or "")
    if not m:
        return None, None
    return int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))


@register("remotive")
class Remotive(Source):
    URL = "https://remotive.com/api/remote-jobs"

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(self.URL)
        if r.status_code != 200:
            return []
        out: list[Job] = []
        for j in r.json().get("jobs", []):
            out.append(self._to_job(j))
        return out

    def _to_job(self, j: dict) -> Job:
        company = j.get("company_name", "")
        slug = _slugify(company)
        desc = _HTML.sub(" ", j.get("description", "") or "")[:3000]
        lo, hi = _parse_salary(j.get("salary", "") or desc)
        posted = None
        if d := j.get("publication_date"):
            try:
                posted = datetime.fromisoformat(d).date()
            except ValueError:
                posted = None
        return Job(
            id=make_id("remotive", slug, str(j["id"])),
            source="remotive",
            company=company,
            title=j.get("title", ""),
            location=j.get("candidate_required_location") or "Remote",
            remote=True,
            salary_min=lo, salary_max=hi,
            url=j.get("url", ""),
            posted_at=posted,
            seen_at=date.today(),
            description_text=desc,
        )
