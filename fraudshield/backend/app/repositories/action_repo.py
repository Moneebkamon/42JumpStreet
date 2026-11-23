"""Actions taken on a case. Today that is only takedown drafts (drafted and exported, never sent)."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS takedown_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_ref TEXT NOT NULL,
    recipient_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    exported_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_drafts_case ON takedown_drafts(case_ref);
"""
_META = "id, case_ref, recipient_type, subject, created_by, created_at, exported_at"


def add_draft(case_ref: str, recipient_type: str, subject: str, body: str, actor: str) -> int:
    with closing(connect(_SCHEMA)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO takedown_drafts (case_ref, recipient_type, subject, body, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (case_ref, recipient_type, subject, body, actor, now_utc()),
        )
        return int(cur.lastrowid)


def list_drafts(case_ref: str) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute(f"SELECT {_META} FROM takedown_drafts WHERE case_ref = ? ORDER BY id", (case_ref,))]


def get_draft(draft_id: int) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute(f"SELECT {_META}, body FROM takedown_drafts WHERE id = ?", (draft_id,)).fetchone()
    return dict(r) if r else None


def mark_exported(draft_id: int) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("UPDATE takedown_drafts SET exported_at = ? WHERE id = ?", (now_utc(), draft_id))
