from datetime import date, timedelta
from jobscraper.job import Job
from jobscraper.store import Store


def _j(jid: str, score: int = 50) -> Job:
    return Job(
        id=jid, source=jid.split(":")[0], company="X", title="T",
        location="Remote", remote=True, salary_min=None, salary_max=None,
        url=f"https://x/{jid}", posted_at=None, seen_at=date.today(),
        description_text="",
        score=score, rationale="ok",
    )


def test_first_seen_today_is_today(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    s.upsert([_j("greenhouse:a:1")])
    new_today, still = s.partition(date.today())
    assert any(j.id == "greenhouse:a:1" for j in new_today)
    assert still == []


def test_re_upsert_moves_to_still_open(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    yesterday = date.today() - timedelta(days=1)
    s.upsert([_j("greenhouse:a:1")], today=yesterday)
    s.upsert([_j("greenhouse:a:1")], today=date.today())
    new_today, still = s.partition(date.today())
    assert new_today == []
    assert any(j.id == "greenhouse:a:1" for j in still)


def test_apply_flag_persists(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    s.upsert([_j("g:a:1")])
    s.mark_applied("g:a:1", notes="quick app")
    rows = s.all_seen()
    row = next(r for r in rows if r["id"] == "g:a:1")
    assert row["applied"] == 1
    assert row["notes"] == "quick app"
