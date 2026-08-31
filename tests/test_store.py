from datetime import date, timedelta
from searchboard.job import Job
from searchboard.store import Store


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


def test_upsert_writes_detail_columns(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    j = _j("greenhouse:a:1")
    j.location = "Remote · US"
    j.salary_min = 120000
    j.salary_max = 150000
    j.posted_at = date.today()
    s.upsert([j])
    r = s._conn.execute("SELECT * FROM seen WHERE id=?", (j.id,)).fetchone()
    assert r["source"] == "greenhouse"
    assert r["location"] == "Remote · US"
    assert r["salary_min"] == 120000
    assert r["salary_max"] == 150000
    assert r["posted_at"] == date.today().isoformat()
    assert r["rationale"] == "ok"


def test_detail_columns_update_on_reupsert(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    s.upsert([_j("greenhouse:a:1")])
    j2 = _j("greenhouse:a:1")
    j2.location = "NYC"
    s.upsert([j2])
    r = s._conn.execute("SELECT location FROM seen WHERE id=?", (j2.id,)).fetchone()
    assert r["location"] == "NYC"


def test_migration_adds_columns_to_legacy_db(tmp_path):
    import sqlite3
    p = tmp_path / "seen.sqlite"
    conn = sqlite3.connect(p)
    conn.execute("""CREATE TABLE seen (
        id TEXT PRIMARY KEY, company TEXT, title TEXT, url TEXT,
        first_seen DATE NOT NULL, last_seen DATE NOT NULL,
        ranked_score INTEGER, applied INTEGER NOT NULL DEFAULT 0, notes TEXT)""")
    conn.execute("INSERT INTO seen VALUES ('x:y:1','C','T','u','2026-01-01','2026-01-01',50,0,'')")
    conn.commit(); conn.close()
    s = Store(p)  # must not raise; must add missing columns
    r = s._conn.execute("SELECT source, location, sent_at FROM seen WHERE id='x:y:1'").fetchone()
    assert r["source"] is None and r["location"] is None


def test_meta_round_trips_and_persists(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    assert s.get_meta("profile_hash") is None
    s.set_meta("profile_hash", "abc")
    assert s.get_meta("profile_hash") == "abc"
    s.set_meta("profile_hash", "def")
    assert Store(tmp_path / "seen.sqlite").get_meta("profile_hash") == "def"


def test_scores_returns_only_ranked_rows(tmp_path):
    s = Store(tmp_path / "seen.sqlite")
    s.upsert([_j("g:a:1", score=80)])
    s._conn.execute(
        "INSERT INTO seen(id, first_seen, last_seen) VALUES ('g:a:2','2026-01-01','2026-01-01')")
    got = s.scores()
    assert got["g:a:1"] == (80, "ok")
    assert "g:a:2" not in got
