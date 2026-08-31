from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path
import sqlite3
from searchboard.job import Job


_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    id              TEXT PRIMARY KEY,
    company         TEXT,
    title           TEXT,
    url             TEXT,
    first_seen      DATE NOT NULL,
    last_seen       DATE NOT NULL,
    ranked_score    INTEGER,
    applied         INTEGER NOT NULL DEFAULT 0,
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS idx_seen_first_seen ON seen(first_seen);
CREATE INDEX IF NOT EXISTS idx_seen_last_seen  ON seen(last_seen);
CREATE TABLE IF NOT EXISTS meta (
    key             TEXT PRIMARY KEY,
    value           TEXT
);
"""


_EXTRA_COLS = [
    ("sent_at", "DATE"),
    ("source", "TEXT"),
    ("location", "TEXT"),
    ("salary_min", "INTEGER"),
    ("salary_max", "INTEGER"),
    ("posted_at", "DATE"),
    ("rationale", "TEXT"),
]


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        for name, typ in _EXTRA_COLS:
            try:
                self._conn.execute(f"ALTER TABLE seen ADD COLUMN {name} {typ}")
            except sqlite3.OperationalError:
                pass
        self._conn.commit()

    def upsert(self, jobs: list[Job], today: date | None = None) -> None:
        today = today or date.today()
        with self._conn:
            for j in jobs:
                self._conn.execute("""
                    INSERT INTO seen(id, company, title, url, first_seen, last_seen,
                                     ranked_score, source, location, salary_min,
                                     salary_max, posted_at, rationale)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        last_seen     = excluded.last_seen,
                        ranked_score  = excluded.ranked_score,
                        title         = excluded.title,
                        url           = excluded.url,
                        source        = excluded.source,
                        location      = excluded.location,
                        salary_min    = excluded.salary_min,
                        salary_max    = excluded.salary_max,
                        posted_at     = excluded.posted_at,
                        rationale     = excluded.rationale
                """, (j.id, j.company, j.title, j.url, today.isoformat(),
                      today.isoformat(), j.score, j.source, j.location,
                      j.salary_min, j.salary_max,
                      j.posted_at.isoformat() if j.posted_at else None,
                      j.rationale))

    def partition(self, today: date) -> tuple[list[Job], list[Job]]:
        """Return (new_today, still_open). 'Still open' = first_seen < today AND last_seen == today."""
        new_rows = self._conn.execute(
            "SELECT * FROM seen WHERE first_seen = ?", (today.isoformat(),)
        ).fetchall()
        still_rows = self._conn.execute(
            "SELECT * FROM seen WHERE first_seen < ? AND last_seen = ?",
            (today.isoformat(), today.isoformat())
        ).fetchall()
        return [self._row_to_job(r) for r in new_rows], [self._row_to_job(r) for r in still_rows]

    def get_meta(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def scores(self) -> dict[str, tuple[int, str | None]]:
        rows = self._conn.execute(
            "SELECT id, ranked_score, rationale FROM seen WHERE ranked_score IS NOT NULL"
        ).fetchall()
        return {r["id"]: (r["ranked_score"], r["rationale"]) for r in rows}

    def all_seen(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("SELECT * FROM seen").fetchall())

    def mark_applied(self, job_id: str, notes: str = "") -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE seen SET applied = 1, notes = ? WHERE id = ?", (notes, job_id)
            )

    def unsent_top(self, today: date, score_floor: int = 50,
                   limit: int = 15, max_age_days: int | None = None) -> list[Job]:
        # posting age uses the board's posted_at, else when we first saw it
        cutoff = ((today - timedelta(days=max_age_days)).isoformat()
                  if max_age_days is not None else "0000-01-01")
        rows = self._conn.execute("""
            SELECT * FROM seen
            WHERE sent_at IS NULL
              AND ranked_score >= ?
              AND last_seen = ?
              AND COALESCE(posted_at, first_seen) >= ?
            ORDER BY ranked_score DESC
            LIMIT ?
        """, (score_floor, today.isoformat(), cutoff, limit)).fetchall()
        return [self._row_to_job(r) for r in rows]

    def mark_sent(self, ids: list[str], today: date) -> None:
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self._conn:
            self._conn.execute(
                f"UPDATE seen SET sent_at = ? WHERE id IN ({placeholders})",
                (today.isoformat(), *ids),
            )

    @staticmethod
    def _row_to_job(r: sqlite3.Row) -> Job:
        return Job(
            id=r["id"], source=r["id"].split(":")[0],
            company=r["company"] or "", title=r["title"] or "",
            location="", remote=False,
            salary_min=None, salary_max=None,
            url=r["url"] or "",
            posted_at=None, seen_at=date.fromisoformat(r["last_seen"]),
            description_text="",
            score=r["ranked_score"], rationale=None,
        )
