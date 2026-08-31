from __future__ import annotations
from datetime import date, datetime
import httpx
from searchboard.job import Job, make_id
from searchboard.sources import register
from searchboard.sources.base import Source


@register("smartrecruiters")
class SmartRecruiters(Source):
    URL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    POSTING_URL = "https://jobs.smartrecruiters.com/{slug}/{id}"
    PAGE_SIZE = 100

    def __init__(self, slugs: list[str], timeout: float = 15.0):
        self.slugs = slugs
        self.timeout = timeout

    def fetch(self) -> list[Job]:
        out: list[Job] = []
        with httpx.Client(timeout=self.timeout) as c:
            for slug in self.slugs:
                out.extend(self._fetch_slug(c, slug))
        return out

    def _fetch_slug(self, c: httpx.Client, slug: str) -> list[Job]:
        jobs: list[Job] = []
        offset = 0
        while True:
            try:
                r = c.get(self.URL.format(slug=slug),
                          params={"limit": self.PAGE_SIZE, "offset": offset})
            except httpx.HTTPError:
                return jobs
            if r.status_code != 200:
                return jobs
            payload = r.json()
            content = payload.get("content") or []
            for j in content:
                jobs.append(self._to_job(slug, j))
            total = payload.get("totalFound", 0)
            offset += len(content)
            if not content or offset >= total:
                return jobs

    def _to_job(self, slug: str, j: dict) -> Job:
        loc = j.get("location") or {}
        full_loc = loc.get("fullLocation") or ""
        remote = bool(loc.get("remote"))
        posted = None
        if rel := j.get("releasedDate"):
            try:
                posted = datetime.fromisoformat(rel.replace("Z", "+00:00")).date()
            except ValueError:
                posted = None
        posting_id = str(j["id"])
        return Job(
            id=make_id("smartrecruiters", slug, posting_id),
            source="smartrecruiters",
            company=(j.get("company") or {}).get("name") or slug,
            title=j.get("name", ""),
            location=full_loc,
            remote=remote,
            salary_min=None, salary_max=None,
            url=self.POSTING_URL.format(slug=slug, id=posting_id),
            posted_at=posted,
            seen_at=date.today(),
            description_text="",
        )
