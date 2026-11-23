"""Admin-changed scoring settings (rule points, band cutoffs), kept on top of the YAML defaults, plus an append-only history."""
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    key TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT NOT NULL
);
"""


def all_values() -> dict[str, str]:
    with closing(connect(_SCHEMA)) as conn:
        return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM settings")}


def set_value(key: str, value: str, actor: str, reason: str) -> None:
    with closing(connect(_SCHEMA)) as conn, conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.execute(
            "INSERT INTO settings (key, value, updated_by, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_by = excluded.updated_by, "
            "updated_at = excluded.updated_at",
            (key, value, actor, now_utc()),
        )
        conn.execute(
            "INSERT INTO settings_history (at, actor, key, old_value, new_value, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (now_utc(), actor, key, row["value"] if row else None, value, reason),
        )


def clear(keys: list[str], actor: str, reason: str) -> int:
    """Remove overrides (back to the YAML default). Returns how many were removed."""
    removed = 0
    with closing(connect(_SCHEMA)) as conn, conn:
        for key in keys:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                conn.execute("DELETE FROM settings WHERE key = ?", (key,))
                conn.execute(
                    "INSERT INTO settings_history (at, actor, key, old_value, new_value, reason) VALUES (?, ?, ?, ?, NULL, ?)",
                    (now_utc(), actor, key, row["value"], reason),
                )
                removed += 1
    return removed


def history(limit: int = 50) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute("SELECT * FROM settings_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
