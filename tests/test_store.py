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


def test_unsent_top_returns_eligible(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    today = date.today()
    s.upsert([
        _j("g:a:1", score=85),
        _j("g:a:2", score=72),
        _j("g:a:3", score=40),
    ], today=today)
    out = s.unsent_top(today, score_floor=50, limit=15)
    ids = [j.id for j in out]
    assert ids == ["g:a:1", "g:a:2"]


def test_unsent_top_excludes_already_sent(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    today = date.today()
    s.upsert([_j("g:a:1", score=85), _j("g:a:2", score=70)], today=today)
    s.mark_sent(["g:a:1"], today)
    out = s.unsent_top(today)
    assert [j.id for j in out] == ["g:a:2"]


def test_unsent_top_excludes_stale_listings(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    s.upsert([_j("g:a:1", score=85)], today=yesterday)
    # not re-upserted today → last_seen stays yesterday
    out = s.unsent_top(today)
    assert out == []


def test_unsent_top_orders_by_score_desc(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    today = date.today()
    s.upsert([
        _j("g:a:1", score=60),
        _j("g:a:2", score=90),
        _j("g:a:3", score=75),
    ], today=today)
    out = s.unsent_top(today)
    assert [j.id for j in out] == ["g:a:2", "g:a:3", "g:a:1"]


def test_unsent_top_respects_limit(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    today = date.today()
    s.upsert([_j(f"g:a:{i}", score=90 - i) for i in range(20)], today=today)
    assert len(s.unsent_top(today, limit=15)) == 15


def test_mark_sent_idempotent(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    today = date.today()
    s.upsert([_j("g:a:1", score=85)], today=today)
    s.mark_sent(["g:a:1"], today)
    s.mark_sent(["g:a:1"], today)  # again
    assert s.unsent_top(today) == []


def test_mark_sent_empty_list_noop(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    s.mark_sent([], date.today())   # should not raise


def test_sent_at_column_migration_idempotent(tmp_path):
    p = tmp_path / "seen.sqlite"
    Store(p)            # creates schema + adds sent_at
    Store(p)            # re-opens, should not error
    Store(p)            # third time for good measure
