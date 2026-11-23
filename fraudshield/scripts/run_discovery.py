"""Replay the recorded/simulated certificate sample through discovery and print the measured figures.

Short-lived: reads the sample, scores, writes data/interim/discovery.db, prints a summary, exits.
Run from the repo root:  backend/.venv/Scripts/python scripts/run_discovery.py [--reset] [--rate N]
  --reset   delete the discovery database first (start clean)
  --rate N  cap at N events per second (default: no cap)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.discovery import domain_watch  # noqa: E402
from app.discovery.ct_stream_listener import DEFAULT_SAMPLE, rate_capped, replay_source  # noqa: E402
from app.discovery.ingest import ingest  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--rate", type=float, default=None)
    ap.add_argument("--sample", default=str(DEFAULT_SAMPLE))
    args = ap.parse_args()

    if args.reset and domain_watch.db_path().exists():
        domain_watch.db_path().unlink()

    summary = ingest(rate_capped(replay_source(args.sample), args.rate), source="ct_replay", simulated=True)
    print(json.dumps({"run": summary, "totals": domain_watch.stats()}, indent=2))


if __name__ == "__main__":
    main()
