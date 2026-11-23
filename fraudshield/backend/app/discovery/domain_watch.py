"""Where discovery results live: a small SQLite file (stdlib only).

This is deliberately temporary. Stage 03 brings the real database; this module is the only place that
knows about the discovery tables, so moving them is a one-file change.

Tables:
- detections: one row per scored domain (also serves as the pre-warmed scan cache)
- runs: one row per ingest run (counts and timings, for the pass-through and latency figures)
"""
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "interim" / "discovery.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    domain TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    simulated INTEGER NOT NULL DEFAULT 0,
    issued_at TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    issue_to_detection_s REAL NOT NULL,
    processing_ms REAL NOT NULL,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    action TEXT NOT NULL,
    brand_id TEXT NOT NULL DEFAULT '',
    brand_name TEXT NOT NULL DEFAULT '',
    prefilter_reasons TEXT NOT NULL,
    reasons TEXT NOT NULL,
    result_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_det_score ON detections(score);
CREATE INDEX IF NOT EXISTS idx_det_detected ON detections(detected_at);
CREATE TABLE IF NOT EXISTS checked (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    source TEXT NOT NULL,
    simulated INTEGER NOT NULL DEFAULT 0,
    kept INTEGER NOT NULL,
    score INTEGER,
    band TEXT NOT NULL DEFAULT '',
    brand_name TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    simulated INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    events INTEGER NOT NULL,
    domains_seen INTEGER NOT NULL,
    kept INTEGER NOT NULL,
    scored INTEGER NOT NULL,
    flagged INTEGER NOT NULL,
    total_processing_ms REAL NOT NULL
);
"""

_LIST_COLUMNS = (
    "domain, source, simulated, issued_at, detected_at, issue_to_detection_s, processing_ms, score, band, "
    "action, brand_id, brand_name, prefilter_reasons, reasons, status"
)


def db_path() -> Path:
    return Path(os.environ.get("FRAUDSHIELD_DISCOVERY_DB", DEFAULT_DB))


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_detection(d: dict, path: Path | None = None) -> bool:
    """Insert a detection. Returns False (and changes nothing) if the domain is already stored."""
    with closing(_connect(path)) as conn, conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO detections (domain, source, simulated, issued_at, detected_at,
               issue_to_detection_s, processing_ms, score, band, action, brand_id, brand_name,
               prefilter_reasons, reasons, result_json)
               VALUES (:domain, :source, :simulated, :issued_at, :detected_at, :issue_to_detection_s,
               :processing_ms, :score, :band, :action, :brand_id, :brand_name,
               :prefilter_reasons, :reasons, :result_json)""",
            {
                **d,
                "simulated": int(d.get("simulated", False)),
                "prefilter_reasons": json.dumps(d["prefilter_reasons"]),
                "reasons": json.dumps(d["reasons"]),
                "result_json": json.dumps(d["result"]),
            },
        )
        return cur.rowcount == 1


CHECKED_KEEP = 1000  # the "recently checked" list is a ring buffer: only the newest rows are kept


def record_checked(rows: list[dict], path: Path | None = None) -> None:
    """Remember which domains were just looked at (kept or not), newest CHECKED_KEEP only."""
    if not rows:
        return
    with closing(_connect(path)) as conn, conn:
        conn.executemany(
            """INSERT INTO checked (domain, checked_at, source, simulated, kept, score, band, brand_name)
               VALUES (:domain, :checked_at, :source, :simulated, :kept, :score, :band, :brand_name)""",
            [{**r, "simulated": int(r.get("simulated", False)), "kept": int(r["kept"])} for r in rows[-CHECKED_KEEP:]],
        )
        conn.execute("DELETE FROM checked WHERE id <= (SELECT MAX(id) FROM checked) - ?", (CHECKED_KEEP,))


def recent_checked(limit: int = 300, path: Path | None = None) -> list[dict]:
    with closing(_connect(path)) as conn:
        rows = conn.execute(
            "SELECT domain, checked_at, source, simulated, kept, score, band, brand_name FROM checked ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, CHECKED_KEEP)),),
        ).fetchall()
    return [{**dict(r), "simulated": bool(r["simulated"]), "kept": bool(r["kept"])} for r in rows]


def is_known(domain: str, path: Path | None = None) -> bool:
    with closing(_connect(path)) as conn:
        return conn.execute("SELECT 1 FROM detections WHERE domain = ?", (domain,)).fetchone() is not None


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["simulated"] = bool(d["simulated"])
    d["prefilter_reasons"] = json.loads(d["prefilter_reasons"])
    d["reasons"] = json.loads(d["reasons"])
    return d


def list_detections(
    min_score: int = 0, brand: str | None = None, source: str | None = None,
    status: str | None = None, limit: int = 50, path: Path | None = None,
) -> list[dict]:
    where, args = ["score >= ?"], [min_score]
    for col, val in (("brand_id", brand), ("source", source), ("status", status)):
        if val:
            where.append(f"{col} = ?")
            args.append(val)
    sql = f"SELECT {_LIST_COLUMNS} FROM detections WHERE {' AND '.join(where)} ORDER BY detected_at DESC, score DESC LIMIT ?"
    with closing(_connect(path)) as conn:
        return [_row(r) for r in conn.execute(sql, [*args, limit])]


def cached_result(domain: str) -> dict | None:
    """The stored scan result for a domain, or None. Read-only: never creates the database file."""
    p = db_path()
    if not p.exists():
        return None
    try:
        with closing(sqlite3.connect(f"file:{p}?mode=ro", uri=True)) as conn:
            row = conn.execute("SELECT result_json FROM detections WHERE domain = ?", (domain,)).fetchone()
    except sqlite3.Error:
        return None
    return json.loads(row[0]) if row else None


def record_run(run: dict, path: Path | None = None) -> None:
    with closing(_connect(path)) as conn, conn:
        conn.execute(
            """INSERT INTO runs (source, simulated, started_at, events, domains_seen, kept, scored, flagged,
               total_processing_ms) VALUES (:source, :simulated, :started_at, :events, :domains_seen, :kept,
               :scored, :flagged, :total_processing_ms)""",
            {**run, "simulated": int(run.get("simulated", False))},
        )


def stats(path: Path | None = None) -> dict:
    with closing(_connect(path)) as conn:
        run = conn.execute(
            """SELECT COALESCE(SUM(events),0) e, COALESCE(SUM(domains_seen),0) s, COALESCE(SUM(kept),0) k,
               COALESCE(SUM(scored),0) sc, COALESCE(SUM(flagged),0) f, COALESCE(SUM(total_processing_ms),0) ms
               FROM runs"""
        ).fetchone()
        det = conn.execute(
            """SELECT COUNT(*) n, COALESCE(AVG(processing_ms),0) avg_ms, COALESCE(AVG(issue_to_detection_s),0) avg_lag,
               COALESCE(MAX(simulated),0) sim FROM detections"""
        ).fetchone()
        bands = {r["band"]: r["n"] for r in conn.execute("SELECT band, COUNT(*) n FROM detections GROUP BY band")}
        brands = [
            {"brand_id": r["brand_id"], "brand_name": r["brand_name"], "count": r["n"]}
            for r in conn.execute(
                """SELECT brand_id, brand_name, COUNT(*) n FROM detections WHERE brand_id != ''
                   GROUP BY brand_id ORDER BY n DESC LIMIT 5"""
            )
        ]
        live = conn.execute(
            """SELECT COALESCE(SUM(events),0) e, MAX(started_at) last FROM runs WHERE simulated = 0"""
        ).fetchone()
        last_live_detection = conn.execute("SELECT MAX(detected_at) FROM detections WHERE simulated = 0").fetchone()[0]
    seen = run["s"]
    return {
        "live_events": live["e"],
        "last_live_run_at": live["last"],
        "last_live_detection_at": last_live_detection,
        "events_processed": run["e"],
        "domains_seen": seen,
        "domains_kept": run["k"],
        "pass_through_rate": round(run["k"] / seen, 4) if seen else 0.0,
        "detections": det["n"],
        "flagged": run["f"],
        "avg_processing_ms": round(det["avg_ms"], 2),
        "avg_issue_to_detection_s": round(det["avg_lag"], 3),
        "by_band": bands,
        "top_brands": brands,
        "simulated": bool(det["sim"]),
    }
