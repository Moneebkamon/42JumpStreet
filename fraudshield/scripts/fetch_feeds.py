"""Load threat feeds into data/interim/threat_feeds.db.

Two ways in:
  1. From a file you already downloaded (no network):
       fetch_feeds.py --file openphish path/to/feed.txt
  2. Download now (network). Prints the plan and does NOTHING until you add --yes:
       fetch_feeds.py --download openphish urlhaus --yes

Check each feed's terms and access rules first. Some require a free account or key (set it in the environment
variable named below) and I have not verified current access rules for any of them.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import httpx  # noqa: E402

from app.analyzers.threat_intel.feed_loader import PARSERS, db_path, load_feed_text  # noqa: E402

FEEDS = {
    "openphish": {"url": "https://openphish.com/feed.txt", "key_env": None, "note": "community feed, URLs only"},
    "urlhaus": {"url": "https://urlhaus.abuse.ch/downloads/csv_online/", "key_env": "URLHAUS_AUTH_KEY",
                "note": "online malware/phishing URLs, CSV; abuse.ch may require a free Auth-Key"},
    "phishtank": {"url": "https://data.phishtank.com/data/online-valid.csv", "key_env": None,
                  "note": "verified phishing, CSV; PhishTank may require a registered app key"},
}


def download(name: str) -> str:
    spec = FEEDS[name]
    headers = {"User-Agent": "fraudshield-feed-loader"}
    if spec["key_env"] and os.environ.get(spec["key_env"]):
        headers["Auth-Key"] = os.environ[spec["key_env"]]
    resp = httpx.get(spec["url"], headers=headers, timeout=60, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", nargs=2, metavar=("SOURCE", "PATH"), help="load a feed file you already have")
    ap.add_argument("--download", nargs="+", choices=sorted(FEEDS), help="download these feeds")
    ap.add_argument("--yes", action="store_true", help="actually download (otherwise only print the plan)")
    args = ap.parse_args()

    if args.file:
        source, path = args.file
        if source not in PARSERS:
            sys.exit(f"unknown source {source}; choose from {sorted(PARSERS)}")
        n = load_feed_text(source, Path(path).read_text(encoding="utf-8", errors="replace"))
        print(f"loaded {n} URLs from {source} into {db_path()}")
        return

    if not args.download:
        ap.print_help()
        return
    print("Plan:")
    for name in args.download:
        print(f"  {name}: GET {FEEDS[name]['url']}  ({FEEDS[name]['note']})")
    if not args.yes:
        print("Dry run only. Re-run with --yes to download.")
        return
    for name in args.download:
        try:
            n = load_feed_text(name, download(name))
            print(f"{name}: loaded {n} URLs into {db_path()}")
        except Exception as exc:  # report and continue with the next feed
            print(f"{name}: FAILED ({type(exc).__name__}: {exc})")


if __name__ == "__main__":
    main()
