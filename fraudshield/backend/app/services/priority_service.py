"""Triage priority = risk x exposure. All weights are hand-set starting values, like the rule weights.

risk      = the scan score (0-100)
exposure  = brand importance x (1 + 0.25 per citizen report, max 4) x (1 + 0.1 per stored scan of the host, max 5)
            x 1.2 if the domain was detected in the last 24 hours
priority  = risk x exposure, capped at 100

The "users hit" input uses stored scans and citizen reports only (browser-extension history is deferred).
"""
from datetime import datetime, timezone

from app.engine.prioritizer import harm_weight
from app.repositories import case_repo, citizen_report_repo, scan_repo
from app.discovery import domain_watch

QUEUE_MIN_SCORE = 30
REPORT_STEP, REPORT_MAX = 0.25, 4
SCAN_STEP, SCAN_MAX = 0.1, 5
RECENT_HOURS, RECENT_BONUS = 24, 1.2


def _recent(detected_at: str | None) -> float:
    if not detected_at:
        return 1.0
    try:
        when = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
    except ValueError:
        return 1.0
    hours = (datetime.now(timezone.utc) - when).total_seconds() / 3600
    return RECENT_BONUS if 0 <= hours <= RECENT_HOURS else 1.0


def compute(score: int, brand_id: str, host: str, detected_at: str | None = None,
            reports: int | None = None, scans: int | None = None) -> dict:
    reports = citizen_report_repo.count_for_host(host) if reports is None else reports
    scans = scan_repo.count_for_host(host) if scans is None else scans
    brand = harm_weight(brand_id)
    recency = _recent(detected_at)
    exposure = brand * (1 + REPORT_STEP * min(reports, REPORT_MAX)) * (1 + SCAN_STEP * min(scans, SCAN_MAX)) * recency
    return {
        "priority": round(min(100.0, score * exposure), 1),
        "risk": score, "reports": reports, "scans": scans,
        "brand_weight": brand, "recency": recency, "exposure": round(exposure, 2),
    }


def triage_queue(limit: int = 100) -> list[dict]:
    """Detections and citizen reports that have no case yet, highest priority first."""
    cased = case_repo.hosts_with_cases()
    reported = citizen_report_repo.reported_hosts()
    items, seen_hosts = [], set()

    for d in domain_watch.list_detections(min_score=QUEUE_MIN_SCORE, limit=200):
        host = d["domain"]
        if host in cased:
            continue
        seen_hosts.add(host)
        b = compute(d["score"], d["brand_id"], host, d["detected_at"], reports=reported.get(host, 0))
        items.append({"kind": "detection", "ref": host, "url": f"https://{host}/", "host": host, "score": d["score"],
                      "band": d["band"], "brand_name": d["brand_name"], "when": d["detected_at"],
                      "priority": b["priority"], "reports": b["reports"]})

    for r in citizen_report_repo.list_recent(200):
        if r["host"] in cased or r["host"] in seen_hosts:
            continue
        seen_hosts.add(r["host"])
        full = citizen_report_repo.get(r["ref"])
        feats = full["result"]["features"] if full else {}
        brand_id = feats.get("brand_id", "") if feats.get("brand_impersonation") else ""
        b = compute(r["score"], brand_id, r["host"], r["created_at"])
        items.append({"kind": "report", "ref": r["ref"], "url": r["url"], "host": r["host"], "score": r["score"],
                      "band": r["band"], "brand_name": feats.get("brand_name", "") if brand_id else "",
                      "when": r["created_at"], "priority": b["priority"], "reports": b["reports"]})

    return sorted(items, key=lambda i: (-i["priority"], i["host"]))[:limit]
