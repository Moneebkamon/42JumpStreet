"""Run certificate events through prefilter -> score -> store -> alert, and measure it.

Scoring here is URL/domain-only (no network lookups, no deep scan): fast, safe to run on every survivor.
A deep scan of the flagged ones is a later step.

Timing: `processing_ms` is the real time spent scoring one domain. `issue_to_detection_s` is the gap between
certificate issue and detection. For a live stream that is wall-clock time. For a replayed sample the
certificate times are in the past, so the gap is simulated as (event time + real processing time).
"""
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone

from app.alerts import dispatcher
from app.discovery import domain_watch
from app.discovery.prefilter import clean_domain, prefilter
from app.engine.pipeline import run_pipeline

MAX_ALERTS_PER_RUN = 5
FLAG_BANDS = dispatcher.ALERT_BANDS


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ingest(
    events: Iterable[dict],
    *,
    source: str = "ct_feed",
    simulated: bool = False,
    notify: Callable[[dict], bool] = dispatcher.notify,
    db_file=None,
) -> dict:
    """Process events and return the run summary (also stored). `db_file` overrides the database path."""
    run = {
        "source": source, "simulated": simulated, "started_at": _iso(datetime.now(timezone.utc)),
        "events": 0, "domains_seen": 0, "kept": 0, "scored": 0, "flagged": 0, "total_processing_ms": 0.0,
    }
    alerts_sent = 0
    seen_here: set[str] = set()
    checked: list[dict] = []  # every distinct domain looked at in this run, for the dashboard's scrollable list

    for event in events:
        run["events"] += 1
        issued = _parse(event["issued_at"])
        for raw in event["domains"]:
            domain = clean_domain(raw)
            domain = domain[4:] if domain.startswith("www.") else domain
            if domain in seen_here:
                continue
            seen_here.add(domain)
            run["domains_seen"] += 1

            seen_row = {"domain": domain, "checked_at": _iso(datetime.now(timezone.utc)), "source": source,
                        "simulated": simulated, "kept": False, "score": None, "band": "", "brand_name": ""}
            checked.append(seen_row)
            pre = prefilter(domain)
            if not pre.keep:
                continue
            run["kept"] += 1
            seen_row["kept"] = True
            if domain_watch.is_known(domain, db_file):
                seen_row["band"] = "known"
                continue

            t0 = time.perf_counter()
            try:
                result = run_pipeline(f"https://{domain}", use_network=False)
            except ValueError:
                continue
            ms = (time.perf_counter() - t0) * 1000
            run["scored"] += 1
            run["total_processing_ms"] += ms

            detected = issued + timedelta(milliseconds=ms) if simulated else datetime.now(timezone.utc)
            brand = result["features"]
            det = {
                "domain": domain, "source": source, "simulated": simulated,
                "issued_at": _iso(issued), "detected_at": _iso(detected),
                "issue_to_detection_s": round((detected - issued).total_seconds(), 3),
                "processing_ms": round(ms, 2),
                "score": result["score"], "band": result["band"], "action": result["action"],
                "brand_id": brand.get("brand_id", "") if brand.get("brand_impersonation") else "",
                "brand_name": brand.get("brand_name", "") if brand.get("brand_impersonation") else "",
                "prefilter_reasons": list(pre.reasons), "reasons": result["reasons"], "result": result,
            }
            domain_watch.save_detection(det, db_file)
            seen_row.update(score=result["score"], band=result["band"], brand_name=det["brand_name"])
            if result["band"] in FLAG_BANDS:
                run["flagged"] += 1
                if alerts_sent < MAX_ALERTS_PER_RUN and notify(det):
                    alerts_sent += 1

    run["total_processing_ms"] = round(run["total_processing_ms"], 2)
    domain_watch.record_checked(checked, db_file)
    domain_watch.record_run(run, db_file)
    return {**run, "alerts_sent": alerts_sent,
            "pass_through_rate": round(run["kept"] / run["domains_seen"], 4) if run["domains_seen"] else 0.0}
