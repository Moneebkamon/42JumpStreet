"""Live early detection: read new certificates from a certstream-compatible server and score the brand-like domains.

Read-only and passive: it only receives domain names (as plain text), scores them from the name, and stores results.
It never contacts the domains it sees. Runs until stopped (Ctrl+C / docker compose stop ct-listener).
Each ~20 s slice is recorded as a run, which is the dashboard's "last seen" heartbeat.

  FRAUDSHIELD_CT_URL=ws://certstream:8080/domains-only  python scripts/run_ct_listener.py [--slice 20]
"""
import argparse
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.discovery.ct_stream_listener import for_seconds, live_source, with_reconnect  # noqa: E402
from app.discovery.ingest import ingest  # noqa: E402

stop = False


def _stop(*_):
    global stop
    stop = True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice", type=float, default=20.0, help="seconds per recorded run (heartbeat interval)")
    args = ap.parse_args()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    failures = 0
    events = with_reconnect(live_source, max_retries=3)  # ONE persistent connection, sliced into runs below
    while not stop:
        try:
            summary = ingest(for_seconds(events, args.slice), source="ct_live", simulated=False)
            failures = 0
            print(json.dumps({k: summary[k] for k in ("events", "domains_seen", "kept", "scored", "flagged")}), flush=True)
        except Exception as exc:  # noqa: BLE001 - keep the service alive, back off, report
            failures += 1
            events = with_reconnect(live_source, max_retries=3)  # the old one is finished after an error
            print(f"stream error ({type(exc).__name__}); retry {failures}", flush=True)
            time.sleep(min(60, 2 ** failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
