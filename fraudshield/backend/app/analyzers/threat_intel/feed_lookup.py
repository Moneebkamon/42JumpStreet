"""Is this URL on a loaded threat feed? Keys start with threat_. Read-only; a missing database means "no".

Matching:
- the exact normalized URL always counts
- the whole host counts too, EXCEPT on shared hosting (github.io, blogspot.com, ...): one bad page there must not
  condemn every other site on the platform, so only an exact URL match counts.
"""
import sqlite3
from contextlib import closing

from app.analyzers.threat_intel.feed_loader import db_path
from app.analyzers.url_analyzer.normalizer import NormalizedURL

SHARED_HOSTING = (
    "github.io", "gitlab.io", "blogspot.com", "wordpress.com", "sites.google.com", "weebly.com", "wixsite.com",
    "netlify.app", "vercel.app", "pages.dev", "workers.dev", "herokuapp.com", "firebaseapp.com", "web.app",
    "000webhostapp.com", "webflow.io", "carrd.co", "godaddysites.com", "square.site", "azurewebsites.net",
    "s3.amazonaws.com", "storage.googleapis.com", "ipfs.io", "dweb.link",
)


def is_shared_hosting(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in SHARED_HOSTING)


def threat_features(n: NormalizedURL) -> dict:
    none = {"threat_listed": 0, "threat_source": ""}
    p = db_path()
    if not p.exists():
        return none
    try:
        with closing(sqlite3.connect(f"file:{p}?mode=ro", uri=True)) as conn:
            row = conn.execute("SELECT source FROM threat_urls WHERE url = ? LIMIT 1", (n.url,)).fetchone()
            if not row and not is_shared_hosting(n.host):
                row = conn.execute("SELECT source FROM threat_urls WHERE host = ? LIMIT 1", (n.host,)).fetchone()
    except sqlite3.Error:
        return none
    return {"threat_listed": 1, "threat_source": row[0]} if row else none
