"""Step 1 of 3 (run with the BACKEND venv). Build a small held-out test set and score it with the current rules.

Positives: the OpenPhish URLs we loaded (fresh, so the ready model cannot have seen them in training).
Negatives: a seeded sample of the Tranco top-1M, in two strata: popular (rank <= 10k, easy) and long tail (harder).
Each positive appears twice: "full" (the whole URL) and "host" (scheme + host only). Negatives are always bare
domains, so "full" lets a model cheat on URL length/path; "host" is the fair comparison.

The rules are run with NO threat-feed database (otherwise every OpenPhish URL would score 85 by lookup) and no network.
These URLs are only parsed and scored as text. Nothing is ever fetched.

Run from the repo root:  backend/.venv/Scripts/python ml/build_eval_set.py
"""
import json
import os
import random
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["FRAUDSHIELD_NETWORK"] = "0"
os.environ["FRAUDSHIELD_THREAT_DB"] = str(Path(tempfile.mkdtemp()) / "none.db")  # lookup disabled: file never exists
sys.path.insert(0, str(ROOT / "backend"))

from app.analyzers.url_analyzer.normalizer import normalize  # noqa: E402
from app.engine.pipeline import run_pipeline  # noqa: E402

OUT = ROOT / "data" / "processed" / "eval_set.jsonl"
N_NEG_PER_STRATUM = 200
SEED = 7


def main() -> None:
    rng = random.Random(SEED)
    con = sqlite3.connect(ROOT / "data" / "interim" / "threat_feeds.db")
    positives = [r[0] for r in con.execute("SELECT url FROM threat_urls WHERE source = 'openphish' ORDER BY url")]

    rows = []
    for url in positives:
        try:
            n = normalize(url)
        except ValueError:
            continue
        rows.append({"url": url, "label": 1, "stratum": "phish", "variant": "full"})
        rows.append({"url": f"{n.scheme}://{n.host}/", "label": 1, "stratum": "phish", "variant": "host"})

    tranco = [ln.split(",", 1)[1] for ln in (ROOT / "data" / "raw" / "tranco" / "top-1m.csv").read_text().splitlines()]
    pools = {"popular": tranco[:10_000], "tail": tranco[10_000:]}
    for stratum, pool in pools.items():
        for d in rng.sample(pool, N_NEG_PER_STRATUM):
            rows.append({"url": f"https://{d}/", "label": 0, "stratum": stratum, "variant": "both"})

    for r in rows:
        try:
            r["rule_score"] = run_pipeline(r["url"], use_network=False)["score"]
        except ValueError:
            r["rule_score"] = None
    rows = [r for r in rows if r["rule_score"] is not None]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    pos = sum(r["label"] for r in rows if r["variant"] == "full")
    print(f"wrote {len(rows)} rows to {OUT} ({pos} phish, {sum(1 for r in rows if r['label'] == 0)} negatives)")


if __name__ == "__main__":
    main()
