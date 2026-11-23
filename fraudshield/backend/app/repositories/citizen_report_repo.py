"""Public reports. They are signals only: storing one never blocks anything."""
import json
from contextlib import closing

from app.db.sqlite import connect, now_utc

_SCHEMA = """
CREATE TABLE IF NOT EXISTS citizen_reports (
    n INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT UNIQUE,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    contact TEXT NOT NULL DEFAULT '',
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_host ON citizen_reports(host);
"""
_COLS = "ref, url, host, note, contact, score, band, created_at"


def add(url: str, host: str, note: str, contact: str, result: dict) -> str:
    with closing(connect(_SCHEMA)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO citizen_reports (url, host, note, contact, score, band, result_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (url, host, note, contact, result["score"], result["band"], json.dumps(result), now_utc()),
        )
        ref = f"CR-{cur.lastrowid:04d}"
        conn.execute("UPDATE citizen_reports SET ref = ? WHERE n = ?", (ref, cur.lastrowid))
    return ref


def get(ref: str) -> dict | None:
    with closing(connect(_SCHEMA)) as conn:
        r = conn.execute(f"SELECT {_COLS}, result_json FROM citizen_reports WHERE ref = ?", (ref,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["result"] = json.loads(d.pop("result_json"))
    return d


def list_recent(limit: int = 100) -> list[dict]:
    with closing(connect(_SCHEMA)) as conn:
        return [dict(r) for r in conn.execute(f"SELECT {_COLS} FROM citizen_reports ORDER BY n DESC LIMIT ?", (limit,))]


def count_for_host(host: str) -> int:
    with closing(connect(_SCHEMA)) as conn:
        return conn.execute("SELECT COUNT(*) FROM citizen_reports WHERE host = ?", (host,)).fetchone()[0]


def reported_hosts() -> dict[str, int]:
    with closing(connect(_SCHEMA)) as conn:
        return {r["host"]: r["c"] for r in conn.execute("SELECT host, COUNT(*) c FROM citizen_reports GROUP BY host")}
