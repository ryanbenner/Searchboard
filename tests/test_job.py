from datetime import date
from searchboard.job import Job, make_id


def test_make_id_format():
    assert make_id("greenhouse", "anthropic", "5483921") == "greenhouse:anthropic:5483921"


def test_make_id_strips_and_lowercases_source_and_slug():
    assert make_id("Greenhouse", "  Anthropic  ", "5483921") == "greenhouse:anthropic:5483921"


def test_job_round_trips_to_dict():
    j = Job(
        id="greenhouse:anthropic:1",
        source="greenhouse",
        company="Anthropic",
        title="Software Engineer",
        location="Remote (US)",
        remote=True,
        salary_min=180000,
        salary_max=280000,
        url="https://example.com/1",
        posted_at=date(2026, 5, 4),
        seen_at=date(2026, 5, 7),
        description_text="hello",
    )
    d = j.to_dict()
    assert d["id"] == "greenhouse:anthropic:1"
    assert d["posted_at"] == "2026-05-04"
    assert d["score"] is None
