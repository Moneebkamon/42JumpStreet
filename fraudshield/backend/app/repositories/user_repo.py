"""Staff accounts. Only a password hash is stored."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def upsert(username: str, password_hash: str, role: str) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash, role = excluded.role",
            (username, password_hash, role, now_utc()),
        )


def get(username: str) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def count() -> int:
    with closing(connect(_SCHEMA)) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
