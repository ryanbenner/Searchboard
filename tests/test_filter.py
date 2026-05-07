from datetime import date
from jobscraper.config import load_profile
from jobscraper.filter import hard_filter
from jobscraper.job import Job
from pathlib import Path


PROFILE = load_profile(Path(__file__).parent / "fixtures" / "profile_min.yml")


def _j(**kw):
    base = dict(
        id="x:y:1", source="x", company="X", title="Software Engineer",
        location="Remote", remote=True, salary_min=None, salary_max=None,
        url="https://x", posted_at=None, seen_at=date.today(),
        description_text="",
    )
    base.update(kw); return Job(**base)


def test_filter_keeps_remote():
    jobs = [_j(remote=True, location="Remote")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_filter_drops_onsite_in_excluded_metro():
    jobs = [_j(remote=False, location="New York, NY")]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_keeps_onsite_in_allowed_metro():
    jobs = [_j(remote=False, location="San Diego, CA")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_filter_drops_director_titles():
    jobs = [_j(title="Director of Engineering")]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_keeps_senior_titles():
    jobs = [_j(title="Senior Software Engineer")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_filter_drops_excluded_keyword():
    jobs = [_j(description_text="Must obtain a secret clearance.")]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_drops_below_salary_floor_when_known():
    jobs = [_j(salary_max=40000)]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_keeps_unknown_salary():
    jobs = [_j(salary_min=None, salary_max=None)]
    assert len(hard_filter(jobs, PROFILE)) == 1
