"""Append-only record of who did what. There is deliberately no update or delete function."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_object ON audit_log(object_type, object_id);
"""


def log(actor: str, action: str, object_type: str, object_id: str, detail: str = "") -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute(
            "INSERT INTO audit_log (at, actor, action, object_type, object_id, detail) VALUES (?, ?, ?, ?, ?, ?)",
            (now_utc(), actor, action, object_type, str(object_id), detail),
        )


def list_recent(limit: int = 100, object_type: str | None = None, object_id: str | None = None) -> list[dict]:
    where, args = [], []
    for col, val in (("object_type", object_type), ("object_id", object_id)):
        if val:
            where.append(f"{col} = ?")
            args.append(val)
    sql = "SELECT id, at, actor, action, object_type, object_id, detail FROM audit_log"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute(sql, [*args, limit])]
