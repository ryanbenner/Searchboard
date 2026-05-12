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


def test_filter_drops_senior_titles():
    jobs = [_j(title="Senior Software Engineer")]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_drops_irrelevant_role():
    jobs = [_j(title="Licensed Therapist")]
    assert hard_filter(jobs, PROFILE) == []


def test_filter_keeps_software_engineer():
    jobs = [_j(title="Software Engineer")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_filter_keeps_intern():
    jobs = [_j(title="Software Engineering Intern")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_filter_keeps_full_stack_developer():
    jobs = [_j(title="Full-Stack Developer")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_keeps_explicit_us_remote():
    jobs = [_j(location="Remote, USA")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_keeps_us_state_remote():
    jobs = [_j(location="Remote - California")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_drops_uk_remote():
    jobs = [_j(location="Remote, UK")]
    assert hard_filter(jobs, PROFILE) == []


def test_us_only_drops_canada_remote():
    jobs = [_j(location="Remote (Canada)")]
    assert hard_filter(jobs, PROFILE) == []


def test_us_only_drops_emea_remote():
    jobs = [_j(location="EMEA Remote")]
    assert hard_filter(jobs, PROFILE) == []


def test_us_only_us_wins_over_canada():
    jobs = [_j(location="Remote, US or Canada")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_keeps_generic_remote():
    jobs = [_j(location="Remote")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_keeps_anywhere():
    jobs = [_j(location="Anywhere")]
    assert len(hard_filter(jobs, PROFILE)) == 1


def test_us_only_keeps_empty_location_when_remote():
    jobs = [_j(location="", remote=True)]
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
