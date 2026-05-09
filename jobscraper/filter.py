from __future__ import annotations
import re
from jobscraper.config import Profile
from jobscraper.job import Job


_RELEVANT_ROLE_RE = re.compile(
    r"\b("
    r"engineer|developer|programmer|"
    r"swe|sde|"
    r"front[\s-]?end|back[\s-]?end|full[\s-]?stack|"
    r"web|mobile|ios|android|"
    r"machine\s+learning|"
    r"data\s+engineer|data\s+scientist|data\s+analyst|"
    r"devops|sre|site\s+reliability|platform|infrastructure|"
    r"new\s+grad|intern"
    r")\b",
    re.IGNORECASE,
)


def _relevant_role(j: Job) -> bool:
    return bool(_RELEVANT_ROLE_RE.search(j.title or ""))


def _location_ok(j: Job, p: Profile) -> bool:
    if j.remote and p.location.remote_ok:
        return True
    if not p.location.onsite_metros:
        return j.remote and p.location.remote_ok
    loc_lower = (j.location or "").lower()
    if any(m.lower() in loc_lower for m in p.location.exclude_metros):
        return False
    return any(m.lower() in loc_lower for m in p.location.onsite_metros)


def _title_ok(j: Job, p: Profile) -> bool:
    t = (j.title or "").lower()
    for band in p.seniority.exclude_bands_hard:
        if re.search(rf"\b{re.escape(band.lower())}\b", t):
            return False
    return True


def _excluded_keyword(j: Job, p: Profile) -> bool:
    blob = f"{j.title}\n{j.description_text}".lower()
    return any(k.lower() in blob for k in p.exclusions.keywords)


def _salary_ok(j: Job, p: Profile) -> bool:
    if j.salary_max is None:
        return True
    return j.salary_max >= p.compensation.min_usd


def _company_ok(j: Job, p: Profile) -> bool:
    return (j.company or "").strip().lower() not in {c.lower() for c in p.exclusions.companies}


def hard_filter(jobs: list[Job], p: Profile) -> list[Job]:
    return [
        j for j in jobs
        if _location_ok(j, p)
        and _title_ok(j, p)
        and _relevant_role(j)
        and not _excluded_keyword(j, p)
        and _salary_ok(j, p)
        and _company_ok(j, p)
    ]
