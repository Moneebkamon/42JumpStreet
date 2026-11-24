"""Links a user visited or researched (from the extension, a message or a manual check)."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

SOURCES = ("extension", "message", "manual")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS link_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visits_user ON link_visits(user_id, created_at);
"""


def add_many(user_id: str, items: list[dict]) -> int:
    rows = [(user_id, i["url"][:2048], i["host"][:255], int(i["score"]), i["band"], i["source"], now_utc()) for i in items]
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.executemany("INSERT INTO link_visits (user_id, url, host, score, band, source, created_at) VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)


def list_for(user_id: str, limit: int = 100, offset: int = 0, source: str | None = None, band: str | None = None) -> list[dict]:
    where, args = "user_id = ?", [user_id]
    if source:
        where += " AND source = ?"
        args.append(source)
    if band:
        where += " AND band = ?"
        args.append(band)
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute(f"SELECT id, url, host, score, band, source, created_at FROM link_visits WHERE {where} "
                            "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?", (*args, limit, offset)).fetchall()
    return [dict(r) for r in rows]


def counts(user_id: str) -> dict:
    with closing(connect(_SCHEMA)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM link_visits WHERE user_id = ?", (user_id,)).fetchone()[0]
        risky = conn.execute("SELECT COUNT(*) FROM link_visits WHERE user_id = ? AND score >= 60", (user_id,)).fetchone()[0]
    return {"visits": total, "risky_visits": risky}


def delete_for_user(user_id: str) -> int:
    with closing(connect(_SCHEMA)) as conn, conn:
        return conn.execute("DELETE FROM link_visits WHERE user_id = ?", (user_id,)).rowcount
