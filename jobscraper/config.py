from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class Seniority(BaseModel):
    years_experience: float
    bands: list[str]
    exclude_bands_hard: list[str]
    exclude_bands_soft: list[str]


class Location(BaseModel):
    remote_ok: bool
    remote_country: Optional[str] = None
    onsite_metros: list[str]
    exclude_metros: list[str] = []


class Compensation(BaseModel):
    min_usd: int
    target_usd: int


class Skills(BaseModel):
    strong: list[str] = []
    some: list[str] = []
    learning: list[str] = []


class Exclusions(BaseModel):
    industries: list[str] = []
    companies: list[str] = []
    keywords: list[str] = []


class Profile(BaseModel):
    name: str
    email: str
    target_roles: list[str]
    seniority: Seniority
    location: Location
    compensation: Compensation
    skills: Skills
    exclusions: Exclusions
    highlights: list[str] = []


def load_profile(path: str | Path) -> Profile:
    data = yaml.safe_load(Path(path).read_text())
    return Profile.model_validate(data)


class CompanyEntry(BaseModel):
    slug: str
    discovered: str  # ISO date
    source: str


class Companies(BaseModel):
    greenhouse: list[CompanyEntry] = []
    lever: list[CompanyEntry] = []
    ashby: list[CompanyEntry] = []
    smartrecruiters: list[CompanyEntry] = []
    disabled: list[str] = []


ATS_KEYS = ("greenhouse", "lever", "ashby", "smartrecruiters")


def load_companies(path: str | Path) -> Companies:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return Companies.model_validate(raw)


def save_companies(c: Companies, path: str | Path) -> None:
    """Write companies.yml. Dedups slugs per-ATS keeping the earliest entry."""
    seen: dict[tuple[str, str], CompanyEntry] = {}
    for ats in ATS_KEYS:
        for e in getattr(c, ats):
            key = (ats, e.slug)
            existing = seen.get(key)
            if existing is None or e.discovered < existing.discovered:
                seen[key] = e
    deduped = Companies(disabled=sorted(set(c.disabled)))
    for (ats, _slug), entry in seen.items():
        getattr(deduped, ats).append(entry)
    for ats in ATS_KEYS:
        getattr(deduped, ats).sort(key=lambda e: e.slug)

    out = {ats: [e.model_dump() for e in getattr(deduped, ats)] for ats in ATS_KEYS}
    out["disabled"] = deduped.disabled
    Path(path).write_text(yaml.safe_dump(out, sort_keys=False))
