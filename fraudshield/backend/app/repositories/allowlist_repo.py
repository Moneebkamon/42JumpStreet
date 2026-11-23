"""Allowlisted domains (reviewed false positives) and the record of which user "this is safe" reports were reviewed."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS allowlist (
    host TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    added_by TEXT NOT NULL,
    added_at TEXT NOT NULL,
    source_scan_id TEXT
);
CREATE TABLE IF NOT EXISTS fp_reviews (
    scan_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,           -- promoted | dismissed
    reviewed_by TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    note TEXT NOT NULL
);
"""


def is_allowlisted(host: str) -> bool:
    with closing(connect(_SCHEMA)) as conn:
        return conn.execute("SELECT 1 FROM allowlist WHERE host = ?", (host,)).fetchone() is not None


def add(host: str, reason: str, actor: str, scan_id: str | None) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute(
            "INSERT INTO allowlist (host, reason, added_by, added_at, source_scan_id) VALUES (?, ?, ?, ?, ?)",
            (host, reason, actor, now_utc(), scan_id),
        )


def remove(host: str) -> bool:
    with closing(connect(_SCHEMA)) as conn, conn:
        return conn.execute("DELETE FROM allowlist WHERE host = ?", (host,)).rowcount > 0


def list_all() -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM allowlist ORDER BY added_at DESC, host")]


def mark_reviewed(scan_id: str, status: str, actor: str, note: str) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO fp_reviews (scan_id, status, reviewed_by, reviewed_at, note) VALUES (?, ?, ?, ?, ?)",
            (scan_id, status, actor, now_utc(), note),
        )


def reviewed_ids() -> set[str]:
    with closing(connect(_SCHEMA)) as conn:
        return {r["scan_id"] for r in conn.execute("SELECT scan_id FROM fp_reviews")}
