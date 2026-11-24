"""Accounts (public users and staff). Only a password hash is stored."""
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


def _conn():
    conn = connect(_SCHEMA)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)")}
    if "email" not in cols:  # accounts created before public sign-up existed
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    return conn


def upsert(username: str, password_hash: str, role: str, email: str | None = None) -> None:
    with closing(_conn()) as conn, conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at, email) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash, role = excluded.role, "
            "email = COALESCE(excluded.email, users.email)",
            (username, password_hash, role, now_utc(), email),
        )


def create(username: str, email: str, password_hash: str, role: str = "user") -> bool:
    """Insert a new account. False if the username or email is already taken."""
    with closing(_conn()) as conn, conn:
        if conn.execute("SELECT 1 FROM users WHERE username = ? OR lower(email) = lower(?)", (username, email)).fetchone():
            return False
        conn.execute("INSERT INTO users (username, password_hash, role, created_at, email) VALUES (?, ?, ?, ?, ?)",
                     (username, password_hash, role, now_utc(), email))
        return True


def get(username: str) -> dict | None:
    with closing(_conn()) as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def set_password(username: str, password_hash: str) -> None:
    with closing(_conn()) as conn, conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))


def count() -> int:
    with closing(_conn()) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
