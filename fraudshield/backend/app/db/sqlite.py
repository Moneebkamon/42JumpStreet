"""Shared helpers for the stdlib-sqlite repositories (SQLAlchemy cannot be imported on this machine; see scan_repo).

All stage 03/09 tables live in one file (FRAUDSHIELD_DB). Each repository passes its own schema.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.repositories.scan_repo import db_path


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(schema: str, path: Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(schema)
    return conn
