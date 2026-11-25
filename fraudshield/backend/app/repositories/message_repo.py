"""Messages (SMS / WhatsApp) the defender checked for a user, and what it did."""
import json
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guarded_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    sender TEXT NOT NULL,
    contact_value TEXT NOT NULL,
    links_json TEXT NOT NULL,
    worst_band TEXT NOT NULL,
    action TEXT NOT NULL,
    emailed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guarded_user ON guarded_messages(user_id, created_at);
"""


def add(user_id: str, channel: str, sender: str, contact_value: str, links: list[dict], worst_band: str, action: str,
        emailed: bool = False) -> int:
    with closing(connect(_SCHEMA)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO guarded_messages (user_id, channel, sender, contact_value, links_json, worst_band, action, emailed, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, channel, sender[:100], contact_value, json.dumps(links), worst_band, action, int(emailed), now_utc()))
        return cur.lastrowid


def list_for(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute("SELECT * FROM guarded_messages WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                            (user_id, limit, offset)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["links"] = json.loads(d.pop("links_json"))
        d["emailed"] = bool(d["emailed"])
        out.append(d)
    return out


def counts(user_id: str) -> dict:
    with closing(connect(_SCHEMA)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM guarded_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
        blocked = conn.execute("SELECT COUNT(*) FROM guarded_messages WHERE user_id = ? AND action = 'blocked'", (user_id,)).fetchone()[0]
    return {"messages": total, "blocked": blocked}
