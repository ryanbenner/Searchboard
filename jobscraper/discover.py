from __future__ import annotations
import re
from datetime import date
from jobscraper.config import Companies, CompanyEntry
from jobscraper.job import Job

_PATTERNS = {
    "greenhouse":      re.compile(r"boards\.greenhouse\.io/([a-z0-9][a-z0-9-]*)", re.I),
    "lever":           re.compile(r"jobs\.lever\.co/([a-z0-9][a-z0-9-]*)", re.I),
    "ashby":           re.compile(r"jobs\.ashbyhq\.com/([a-z0-9][a-z0-9-]*)", re.I),
    "smartrecruiters": re.compile(r"jobs\.smartrecruiters\.com/([A-Za-z0-9][A-Za-z0-9-]*)"),
}


def discover_new_slugs(jobs: list[Job], existing: Companies) -> set[tuple[str, str]]:
    """Return set of (ats, slug) tuples observed in jobs but not yet in companies.yml."""
    known: dict[str, set[str]] = {
        "greenhouse":      {e.slug for e in existing.greenhouse},
        "lever":           {e.slug for e in existing.lever},
        "ashby":           {e.slug for e in existing.ashby},
        "smartrecruiters": {e.slug.lower() for e in existing.smartrecruiters},
    }
    disabled = set(existing.disabled)
    found: set[tuple[str, str]] = set()
    for j in jobs:
        haystack = f"{j.url}\n{j.description_text}"
        for ats, pat in _PATTERNS.items():
            for m in pat.finditer(haystack):
                raw = m.group(1)
                # SmartRecruiters slugs are case-sensitive (e.g. "Visa"); the
                # other ATSes use all-lowercase slugs in their APIs.
                slug = raw if ats == "smartrecruiters" else raw.lower()
                if slug.lower() in {s.lower() for s in known[ats]}:
                    continue
                if f"{ats}:{slug.lower()}" in disabled:
                    continue
                found.add((ats, slug))
    return found


def merge_into_companies(c: Companies, new: set[tuple[str, str]], source_label: str) -> Companies:
    today = date.today().isoformat()
    for ats, slug in new:
        getattr(c, ats).append(CompanyEntry(slug=slug, discovered=today, source=source_label))
    return c
