from dataclasses import dataclass, asdict, field
from datetime import date
from typing import Optional


def make_id(source: str, slug: str, posting_id: str) -> str:
    return f"{source.strip().lower()}:{slug.strip().lower()}:{posting_id.strip()}"


@dataclass
class Job:
    id: str
    source: str
    company: str
    title: str
    location: str
    remote: bool
    salary_min: Optional[int]
    salary_max: Optional[int]
    url: str
    posted_at: Optional[date]
    seen_at: date
    description_text: str
    score: Optional[int] = None
    rationale: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("posted_at", "seen_at"):
            v = d.get(k)
            d[k] = v.isoformat() if isinstance(v, date) else v
        return d
