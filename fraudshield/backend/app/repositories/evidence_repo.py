"""Frozen evidence items. Content is stored exactly as hashed; verification recomputes the hash from storage."""
from contextlib import closing

from app.db.sqlite import connect

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_ref TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    captured_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_ref);
"""
_META = "id, case_ref, kind, sha256, captured_at, tool_version, captured_by, length(content) AS size_bytes"


def add(case_ref: str, kind: str, content: str, sha256: str, captured_at: str, tool_version: str, actor: str) -> int:
    with closing(connect(_SCHEMA)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO evidence (case_ref, kind, content, sha256, captured_at, tool_version, captured_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (case_ref, kind, content, sha256, captured_at, tool_version, actor),
        )
        return int(cur.lastrowid)


def list_for_case(case_ref: str) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute(f"SELECT {_META} FROM evidence WHERE case_ref = ? ORDER BY id", (case_ref,))]


def get(evidence_id: int) -> dict | None:
    """Metadata plus the stored content text."""
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute(f"SELECT {_META}, content FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
    return dict(r) if r else None
