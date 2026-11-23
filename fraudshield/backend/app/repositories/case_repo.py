"""Cases and their event history (status changes, notes, evidence, drafts)."""
import json
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    n INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT UNIQUE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    source TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    status TEXT NOT NULL,
    priority REAL NOT NULL DEFAULT 0,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    brand_id TEXT NOT NULL DEFAULT '',
    brand_name TEXT NOT NULL DEFAULT '',
    result_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cases_host ON cases(host);
CREATE TABLE IF NOT EXISTS case_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_ref TEXT NOT NULL,
    kind TEXT NOT NULL,
    actor TEXT NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    from_status TEXT,
    to_status TEXT,
    at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_case ON case_events(case_ref);
"""
_LIST_COLS = ("ref, title, url, host, source, status, priority, score, band, brand_id, brand_name, created_by, "
              "created_at, updated_at")


def create(*, title: str, url: str, host: str, source: str, source_ref: str, status: str, priority: float,
           score: int, band: str, brand_id: str, brand_name: str, result: dict, actor: str) -> str:
    now = now_utc()
    with closing(connect(_SCHEMA)) as conn, conn:
        cur = conn.execute(
            """INSERT INTO cases (title, url, host, source, source_ref, status, priority, score, band, brand_id,
               brand_name, result_json, created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, url, host, source, source_ref, status, priority, score, band, brand_id, brand_name,
             json.dumps(result), actor, now, now),
        )
        ref = f"FS-{cur.lastrowid:04d}"
        conn.execute("UPDATE cases SET ref = ? WHERE n = ?", (ref, cur.lastrowid))
        conn.execute("INSERT INTO case_events (case_ref, kind, actor, text, to_status, at) VALUES (?, 'created', ?, ?, ?, ?)",
                     (ref, actor, f"Case opened from {source}", status, now))
    return ref


def get(ref: str) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute(f"SELECT {_LIST_COLS}, result_json FROM cases WHERE ref = ?", (ref,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_cases(status: str | None = None, limit: int = 100) -> list[dict]:
    sql, args = f"SELECT {_LIST_COLS} FROM cases", []
    if status:
        sql += " WHERE status = ?"
        args.append(status)
    sql += " ORDER BY priority DESC, n DESC LIMIT ?"
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute(sql, [*args, limit])]


def open_case_for_host(host: str, open_statuses: tuple[str, ...]) -> str | None:
    marks = ",".join("?" * len(open_statuses))
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute(f"SELECT ref FROM cases WHERE host = ? AND status IN ({marks}) ORDER BY n DESC LIMIT 1",
                         (host, *open_statuses)).fetchone()
    return r["ref"] if r else None


def hosts_with_cases() -> set[str]:
    with closing(connect(_SCHEMA)) as conn:
        return {r["host"] for r in conn.execute("SELECT DISTINCT host FROM cases")}


def set_status(ref: str, from_status: str, to_status: str, actor: str, reason: str) -> None:
    now = now_utc()
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE ref = ?", (to_status, now, ref))
        conn.execute(
            "INSERT INTO case_events (case_ref, kind, actor, text, from_status, to_status, at) VALUES (?, 'status', ?, ?, ?, ?, ?)",
            (ref, actor, reason, from_status, to_status, now),
        )


def add_event(ref: str, kind: str, actor: str, text: str) -> None:
    now = now_utc()
    with closing(connect(_SCHEMA)) as conn, conn:
        conn.execute("INSERT INTO case_events (case_ref, kind, actor, text, at) VALUES (?, ?, ?, ?, ?)",
                     (ref, kind, actor, text, now))
        conn.execute("UPDATE cases SET updated_at = ? WHERE ref = ?", (now, ref))


def events(ref: str) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        rows = conn.execute(
            "SELECT id, kind, actor, text, from_status, to_status, at FROM case_events WHERE case_ref = ? ORDER BY id",
            (ref,),
        ).fetchall()
    return [dict(r) for r in rows]
