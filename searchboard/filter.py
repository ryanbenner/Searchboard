from __future__ import annotations
import re
from searchboard.config import Profile
from searchboard.job import Job


_US_TOKEN_RE = re.compile(
    r"\b("
    r"USA|US|U\.S\.|United\s+States|America|"
    r"AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|"
    r"ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|"
    r"OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|"
    r"New\s+York|Los\s+Angeles|San\s+Francisco|Chicago|Boston|"
    r"Seattle|Austin|Denver|Atlanta|Miami|Portland|"
    r"San\s+Diego|Orange\s+County|Irvine"
    r")\b"
)

_NON_US_TOKEN_RE = re.compile(
    r"\b("
    r"UK|United\s+Kingdom|Britain|England|Scotland|Ireland|"
    r"Canada|Canadian|Toronto|Vancouver|Montreal|"
    r"EU|Europe|European|EMEA|EEA|Eurozone|"
    r"Germany|France|Spain|Italy|Netherlands|Sweden|Norway|"
    r"Denmark|Finland|Poland|Portugal|Switzerland|Austria|Belgium|"
    r"APAC|Asia|Japan|China|Singapore|Hong\s+Kong|Korea|"
    r"India|Pakistan|Bangladesh|"
    r"Australia|New\s+Zealand|"
    r"LATAM|Latin\s+America|Mexico|Brazil|Argentina|Colombia|Chile|"
    r"Africa|South\s+Africa|Egypt|Nigeria|Kenya|"
    r"Middle\s+East|UAE|Dubai|Saudi|Israel"
    r")\b"
)

_GENERIC_REMOTE_RE = re.compile(
    r"\b(remote|anywhere|worldwide|global|distributed)\b",
    re.IGNORECASE,
)


def _remote_country_ok(j: Job, p: Profile) -> bool:
    if getattr(p.location, "remote_country", None) != "US":
        return True
    loc = j.location or ""
    if _US_TOKEN_RE.search(loc):
        return True
    if _NON_US_TOKEN_RE.search(loc):
        return False
    if _GENERIC_REMOTE_RE.search(loc) or not loc.strip():
        return True
    return False


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
        return _remote_country_ok(j, p)
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
