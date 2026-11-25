"""Emails and phone numbers a user asked Manee to watch."""
import re
import sqlite3
from contextlib import closing

from app.db.sqlite import connect, now_utc

KINDS = ("email", "phone", "whatsapp")
MAX_PER_USER = 10
_SCHEMA = """
CREATE TABLE IF NOT EXISTS watch_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, kind, value)
);
CREATE INDEX IF NOT EXISTS idx_watch_value ON watch_contacts(value);
"""
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_phone(raw: str, default_cc: str = "971") -> str:
    """Return E.164 (+<digits>) or raise ValueError. A leading 0 means a local number in `default_cc` (UAE)."""
    s = re.sub(r"[\s().-]", "", raw.strip())
    if s.startswith("00"):
        s = "+" + s[2:]
    elif s.startswith("0"):
        s = "+" + default_cc + s[1:]
    elif not s.startswith("+"):
        s = "+" + s
    if not re.fullmatch(r"\+[1-9]\d{7,14}", s):
        raise ValueError("Enter the phone number with country code, e.g. +971501234567.")
    return s


def normalize(kind: str, value: str) -> str:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    if kind == "email":
        v = value.strip().lower()
        if not _EMAIL.match(v) or len(v) > 200:
            raise ValueError("Enter a valid email address.")
        return v
    return normalize_phone(value)


def add(user_id: str, kind: str, value: str) -> dict:
    """Raises ValueError for bad input, a duplicate, or too many contacts."""
    v = normalize(kind, value)
    with closing(connect(_SCHEMA)) as conn, conn:
        if conn.execute("SELECT COUNT(*) FROM watch_contacts WHERE user_id = ?", (user_id,)).fetchone()[0] >= MAX_PER_USER:
            raise ValueError(f"You can watch up to {MAX_PER_USER} contacts.")
        try:
            cur = conn.execute("INSERT INTO watch_contacts (user_id, kind, value, created_at) VALUES (?, ?, ?, ?)",
                               (user_id, kind, v, now_utc()))
        except sqlite3.IntegrityError as exc:
            raise ValueError("That contact is already on your list.") from exc
        return {"id": cur.lastrowid, "kind": kind, "value": v, "verified": False}


def list_for(user_id: str) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute("SELECT id, kind, value, verified, created_at FROM watch_contacts WHERE user_id = ? ORDER BY id",
                            (user_id,)).fetchall()
    return [{**dict(r), "verified": bool(r["verified"])} for r in rows]


def remove(user_id: str, contact_id: int) -> bool:
    with closing(connect(_SCHEMA)) as conn, conn:
        return conn.execute("DELETE FROM watch_contacts WHERE id = ? AND user_id = ?", (contact_id, user_id)).rowcount == 1


def owners_of_number(e164: str) -> list[dict]:
    """Every watched phone/whatsapp entry for this number (several accounts may watch the same one)."""
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute("SELECT id, user_id, kind, value FROM watch_contacts WHERE value = ? AND kind IN ('phone','whatsapp')",
                            (e164,)).fetchall()
    return [dict(r) for r in rows]


def emails_for(user_id: str) -> list[str]:
    return [c["value"] for c in list_for(user_id) if c["kind"] == "email"]
