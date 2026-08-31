from datetime import date
from searchboard.config import Companies, CompanyEntry
from searchboard.discover import discover_new_slugs
from searchboard.job import Job


def _job(desc: str = "", url: str = "https://example.com") -> Job:
    return Job(
        id="x:y:1", source="x", company="X", title="t",
        location="", remote=False, salary_min=None, salary_max=None,
        url=url, posted_at=None, seen_at=date.today(),
        description_text=desc,
    )


def test_discover_finds_new_greenhouse_slug():
    existing = Companies(greenhouse=[CompanyEntry(slug="anthropic", discovered="2026-05-06", source="seed")])
    jobs = [_job(desc="Apply at https://boards.greenhouse.io/stripe/jobs/123")]
    new = discover_new_slugs(jobs, existing)
    assert ("greenhouse", "stripe") in new


def test_discover_ignores_existing():
    existing = Companies(greenhouse=[CompanyEntry(slug="stripe", discovered="2026-05-06", source="seed")])
    jobs = [_job(url="https://boards.greenhouse.io/stripe/jobs/123")]
    assert discover_new_slugs(jobs, existing) == set()


def test_discover_ignores_disabled():
    existing = Companies(disabled=["greenhouse:stripe"])
    jobs = [_job(url="https://boards.greenhouse.io/stripe/jobs/123")]
    assert discover_new_slugs(jobs, existing) == set()
