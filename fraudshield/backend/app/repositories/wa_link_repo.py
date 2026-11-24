# TODO(DELETE LATER - privacy): switched off, nothing routes here any more. Reading WhatsApp / SMS / email messages is a privacy risk. Delete with the other files listed in PRIVACY_DELETE_LATER.md.
"""Which gateway instance (and phone number) belongs to which account. One link per account."""
import hashlib
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS whatsapp_links (
    user_id TEXT PRIMARY KEY,
    instance TEXT NOT NULL UNIQUE,
    number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'connecting',
    created_at TEXT NOT NULL
);
"""


def instance_name(user_id: str) -> str:
    """A stable name that does not reveal the username."""
    return "manee-" + hashlib.sha256(user_id.encode()).hexdigest()[:14]


def get(user_id: str) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute("SELECT * FROM whatsapp_links WHERE user_id = ?", (user_id,)).fetchone()
    return dict(r) if r else None


def get_by_instance(instance: str) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute("SELECT * FROM whatsapp_links WHERE instance = ?", (instance,)).fetchone()
    return dict(r) if r else None


def upsert(user_id: str, number: str, status: str = "connecting") -> dict:
    inst = instance_name(user_id)
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("INSERT INTO whatsapp_links (user_id, instance, number, status, created_at) VALUES (?,?,?,?,?) "
                     "ON CONFLICT(user_id) DO UPDATE SET number = excluded.number, status = excluded.status",
                     (user_id, inst, number, status, now_utc()))
    return {"user_id": user_id, "instance": inst, "number": number, "status": status}


def set_status(user_id: str, status: str) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("UPDATE whatsapp_links SET status = ? WHERE user_id = ?", (status, user_id))


def delete(user_id: str) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("DELETE FROM whatsapp_links WHERE user_id = ?", (user_id,))


def count() -> int:
    with closing(connect(_SCHEMA)) as conn:
        return conn.execute("SELECT COUNT(*) FROM whatsapp_links").fetchone()[0]
