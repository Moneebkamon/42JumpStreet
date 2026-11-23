"""Stored scans. The only module that knows the scans table (stdlib sqlite3).

Why not SQLAlchemy: its compiled extension is blocked by this machine's Windows Application Control policy, so it
cannot even be imported here. If the project later moves to Postgres, this file is the one to rewrite.
"""
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "interim" / "fraudshield.db"
FEEDBACK_LABELS = ("scam", "safe")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    action TEXT NOT NULL,
    confidence REAL NOT NULL,
    deep INTEGER NOT NULL DEFAULT 0,
    cached INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    result_json TEXT NOT NULL,
    feedback TEXT,
    feedback_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
CREATE INDEX IF NOT EXISTS idx_scans_host ON scans(host);
"""
_SUMMARY = "id, url, score, band, action, deep, cached, created_at, feedback"


def db_path() -> Path:
    return Path(os.environ.get("FRAUDSHIELD_DB", DEFAULT_DB))


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save(scan: dict, host: str, deep: bool, path: Path | None = None) -> None:
    """Store a finished scan response (the dict scan_service returns)."""
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            """INSERT OR REPLACE INTO scans (id, url, host, score, band, action, confidence, deep, cached,
               created_at, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (scan["scan_id"], scan["url"], host, scan["score"], scan["band"], scan["action"], scan["confidence"],
             int(deep), int(bool(scan.get("cached"))), _now(), json.dumps(scan)),
        )


def _summary(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["scan_id"] = d.pop("id")
    d["deep"], d["cached"] = bool(d["deep"]), bool(d["cached"])
    return d


def get(scan_id: str, path: Path | None = None) -> dict | None:
    """The full stored result, plus created_at and feedback; None if unknown."""
    with closing(_connect(path)) as conn:
        r = conn.execute("SELECT result_json, created_at, feedback FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if not r:
        return None
    return {**json.loads(r["result_json"]), "created_at": r["created_at"], "feedback": r["feedback"]}


def list_recent(limit: int = 50, offset: int = 0, min_score: int = 0, path: Path | None = None) -> list[dict]:
    with closing(_connect(path)) as conn:
        rows = conn.execute(
            f"SELECT {_SUMMARY} FROM scans WHERE score >= ? ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
            (min_score, limit, offset),
        ).fetchall()
    return [_summary(r) for r in rows]


def flagged_but_marked_safe(limit: int = 100, path: Path | None = None) -> list[dict]:
    """Scans that scored suspicious or worse but a person marked 'safe' (candidate false positives), newest first."""
    with closing(_connect(path)) as conn:
        rows = conn.execute(
            "SELECT id, url, host, score, band, created_at, feedback_at FROM scans "
            "WHERE feedback = 'safe' AND score >= 30 ORDER BY feedback_at DESC, rowid DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{**dict(r), "scan_id": r["id"]} for r in rows]


def recent_results(limit: int = 300, path: Path | None = None) -> list[dict]:
    """Full stored results (with features) of the newest scans; used to preview scoring changes."""
    with closing(_connect(path)) as conn:
        rows = conn.execute("SELECT id, result_json FROM scans ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = json.loads(r["result_json"])
        out.append({"scan_id": r["id"], "url": d.get("url", ""), "score": d.get("score", 0), "band": d.get("band", "safe"),
                    "features": d.get("features") or {}})
    return out


def set_feedback(scan_id: str, label: str, path: Path | None = None) -> bool:
    """Record a human verdict ('scam' or 'safe') on a scan. False if the scan does not exist."""
    if label not in FEEDBACK_LABELS:
        raise ValueError(f"label must be one of {FEEDBACK_LABELS}")
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute("UPDATE scans SET feedback = ?, feedback_at = ? WHERE id = ?", (label, _now(), scan_id))
        return cur.rowcount == 1


def count_for_host(host: str, path: Path | None = None) -> int:
    with closing(_connect(path)) as conn:
        return conn.execute("SELECT COUNT(*) FROM scans WHERE host = ?", (host,)).fetchone()[0]
