"""Parse threat-feed files and keep them in a small local SQLite table. No network code here.

Supported formats (the text of each feed, as downloaded):
- openphish: one URL per line
- urlhaus:   CSV with '#' comment lines; columns id,dateadded,url,url_status,last_online,threat,tags,link,reporter
- phishtank: CSV with a header row; uses the `url` column and keeps rows where `verified` is "yes"

Loading a source replaces that source's old rows, so a refresh never leaves stale entries behind.
"""
import csv
import io
import os
import sqlite3
from collections.abc import Callable
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.analyzers.url_analyzer.normalizer import normalize

DEFAULT_DB = Path(__file__).resolve().parents[4] / "data" / "interim" / "threat_feeds.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS threat_urls (
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    source TEXT NOT NULL,
    loaded_at TEXT NOT NULL,
    PRIMARY KEY (url, source)
);
CREATE INDEX IF NOT EXISTS idx_threat_host ON threat_urls(host);
"""


def db_path() -> Path:
    return Path(os.environ.get("FRAUDSHIELD_THREAT_DB", DEFAULT_DB))


def parse_openphish(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def parse_urlhaus(text: str) -> list[str]:
    body = "\n".join(ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#"))
    urls = []
    for row in csv.reader(io.StringIO(body)):
        if len(row) >= 3 and row[2].startswith(("http://", "https://")):
            urls.append(row[2])
    return urls


def parse_phishtank(text: str) -> list[str]:
    urls = []
    for row in csv.DictReader(io.StringIO(text)):
        if (row.get("verified") or "yes").strip().lower() == "yes" and row.get("url"):
            urls.append(row["url"].strip())
    return urls


PARSERS: dict[str, Callable[[str], list[str]]] = {
    "openphish": parse_openphish,
    "urlhaus": parse_urlhaus,
    "phishtank": parse_phishtank,
}


def load_urls(source: str, urls: list[str], path: Path | None = None) -> int:
    """Replace everything stored for `source` with `urls`. Returns how many usable URLs were stored."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = {}
    for raw in urls:
        try:
            n = normalize(raw)
        except ValueError:
            continue
        rows[n.url] = (n.url, n.host, source, now)

    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(p)) as conn, conn:
        conn.executescript(_SCHEMA)
        conn.execute("DELETE FROM threat_urls WHERE source = ?", (source,))
        conn.executemany("INSERT INTO threat_urls (url, host, source, loaded_at) VALUES (?, ?, ?, ?)", rows.values())
    return len(rows)


def load_feed_text(source: str, text: str, path: Path | None = None) -> int:
    if source not in PARSERS:
        raise ValueError(f"unknown feed source: {source}")
    return load_urls(source, PARSERS[source](text), path)
