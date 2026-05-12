from datetime import date, datetime
import re
import httpx
from jobscraper.job import Job, make_id
from jobscraper.sources import register
from jobscraper.sources.base import Source

_HTML = re.compile(r"<[^>]+>")


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "unknown"


@register("remoteok")
class RemoteOK(Source):
    URL = "https://remoteok.com/api"
    UA = "JobScraper/0.2 (+https://github.com/ryanbenner/JobScraper)"

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        with httpx.Client(timeout=self.timeout, headers={"User-Agent": self.UA}) as c:
            r = c.get(self.URL)
        if r.status_code != 200:
            return []
        out: list[Job] = []
        for j in r.json():
            if "id" not in j or "position" not in j:
                continue
            out.append(self._to_job(j))
        return out

    def _to_job(self, j: dict) -> Job:
        company = j.get("company", "")
        slug = _slugify(company)
        desc = _HTML.sub(" ", j.get("description", "") or "")[:3000]
        posted = None
        if d := j.get("date"):
            try:
                posted = datetime.fromisoformat(d).date()
            except ValueError:
                posted = None
        return Job(
            id=make_id("remoteok", slug, str(j["id"])),
            source="remoteok",
            company=company,
            title=j.get("position", ""),
            location=j.get("location") or "Remote",
            remote=True,
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            url=j.get("url", ""),
            posted_at=posted,
            seen_at=date.today(),
            description_text=desc,
        )
