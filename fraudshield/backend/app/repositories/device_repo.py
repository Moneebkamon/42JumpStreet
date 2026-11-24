"""Devices (browser extensions) linked to an account by a token, plus the per-user switches."""
import hashlib
import secrets
from contextlib import closing

from app.db.sqlite import connect, now_utc

MAX_DEVICES = 5
_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_seen TEXT
);
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    extension_enabled INTEGER NOT NULL DEFAULT 1,
    alerts_enabled INTEGER NOT NULL DEFAULT 1
);
"""


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create(user_id: str, label: str) -> tuple[int, str]:
    """Returns (device id, plain token). The token is shown once; only its hash is stored."""
    with closing(connect(_SCHEMA)) as conn, conn:
        if conn.execute("SELECT COUNT(*) FROM devices WHERE user_id = ?", (user_id,)).fetchone()[0] >= MAX_DEVICES:
            raise ValueError(f"You can link up to {MAX_DEVICES} devices. Remove one first.")
        token = "fsd_" + secrets.token_urlsafe(32)
        cur = conn.execute("INSERT INTO devices (user_id, token_hash, label, created_at) VALUES (?,?,?,?)",
                           (user_id, _hash(token), label[:60] or "Browser", now_utc()))
        return cur.lastrowid, token


def user_for_token(token: str) -> str | None:
    with closing(connect(_SCHEMA)) as conn, conn:
        r = conn.execute("SELECT id, user_id FROM devices WHERE token_hash = ?", (_hash(token),)).fetchone()
        if not r:
            return None
        conn.execute("UPDATE devices SET last_seen = ? WHERE id = ?", (now_utc(), r["id"]))
        return r["user_id"]


def list_for(user_id: str) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute("SELECT id, label, created_at, last_seen FROM devices WHERE user_id = ? ORDER BY id", (user_id,)).fetchall()
    return [dict(r) for r in rows]


def remove(user_id: str, device_id: int) -> bool:
    with closing(connect(_SCHEMA)) as conn, conn:
        return conn.execute("DELETE FROM devices WHERE id = ? AND user_id = ?", (device_id, user_id)).rowcount == 1


def get_settings(user_id: str) -> dict:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute("SELECT extension_enabled, alerts_enabled FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    return {"extension_enabled": bool(r["extension_enabled"]) if r else True,
            "alerts_enabled": bool(r["alerts_enabled"]) if r else True}


def set_settings(user_id: str, extension_enabled: bool | None = None, alerts_enabled: bool | None = None) -> dict:
    cur = get_settings(user_id)
    if extension_enabled is not None:
        cur["extension_enabled"] = extension_enabled
    if alerts_enabled is not None:
        cur["alerts_enabled"] = alerts_enabled
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("INSERT INTO user_settings (user_id, extension_enabled, alerts_enabled) VALUES (?,?,?) "
                     "ON CONFLICT(user_id) DO UPDATE SET extension_enabled = excluded.extension_enabled, "
                     "alerts_enabled = excluded.alerts_enabled",
                     (user_id, int(cur["extension_enabled"]), int(cur["alerts_enabled"])))
    return cur
