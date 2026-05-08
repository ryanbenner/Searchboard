from __future__ import annotations
import json
import os
from typing import Any
from jobscraper.config import Profile
from jobscraper.job import Job

MODEL = "claude-haiku-4-5"
BATCH_SIZE = 40

_TOOL = {
    "name": "submit_rankings",
    "description": "Return a ranking score (0-100) and a one-line rationale for each job.",
    "input_schema": {
        "type": "object",
        "properties": {
            "rankings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":        {"type": "string"},
                        "score":     {"type": "integer", "minimum": 0, "maximum": 100},
                        "rationale": {"type": "string"},
                    },
                    "required": ["id", "score", "rationale"],
                },
            }
        },
        "required": ["rankings"],
    },
}


def _profile_to_text(p: Profile) -> str:
    return (
        f"You are ranking job postings for the following candidate. "
        f"Score 0-100 based on fit. Heavily reward role/skill match, location match, "
        f"and seniority match. Downscore (do NOT zero) jobs in soft-exclude bands "
        f"({', '.join(p.seniority.exclude_bands_soft)}). One-line rationale per job.\n\n"
        f"--- Candidate ---\n"
        f"Name: {p.name}\nEmail: {p.email}\n"
        f"Years experience: {p.seniority.years_experience}\n"
        f"Target roles: {', '.join(p.target_roles)}\n"
        f"Strong skills: {', '.join(p.skills.strong)}\n"
        f"Some skills: {', '.join(p.skills.some)}\n"
        f"Learning: {', '.join(p.skills.learning)}\n"
        f"Location: remote_ok={p.location.remote_ok}; onsite={', '.join(p.location.onsite_metros)}\n"
        f"Compensation: floor=${p.compensation.min_usd}, target=${p.compensation.target_usd}\n"
        f"Highlights: {' | '.join(p.highlights)}\n"
    )


def _job_to_payload(j: Job) -> dict[str, Any]:
    return {
        "id": j.id,
        "company": j.company,
        "title": j.title,
        "location": j.location,
        "remote": j.remote,
        "salary_min": j.salary_min,
        "salary_max": j.salary_max,
        "description": j.description_text[:2000],
    }


def rank_jobs(jobs: list[Job], profile: Profile, client=None) -> list[Job]:
    if not jobs:
        return jobs
    if client is None:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system_blocks = [{
        "type": "text",
        "text": _profile_to_text(profile),
        "cache_control": {"type": "ephemeral"},
    }]

    rankings: dict[str, dict] = {}
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i:i + BATCH_SIZE]
        user_payload = json.dumps([_job_to_payload(j) for j in batch], ensure_ascii=False)
        msg = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_blocks,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "submit_rankings"},
            messages=[{"role": "user", "content":
                f"Rank these {len(batch)} jobs. Return one entry per id. JSON jobs:\n{user_payload}"}],
        )
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                for r in block.input.get("rankings", []):
                    rankings[r["id"]] = r

    out: list[Job] = []
    for j in jobs:
        r = rankings.get(j.id)
        if r:
            j.score = int(r["score"])
            j.rationale = r["rationale"][:240]
        out.append(j)
    return out
