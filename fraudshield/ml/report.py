"""Step 3 of 3 (plain Python, any venv). Compare the rules and the ready model on the held-out set.

Run from the repo root:  python ml/report.py
Reads data/processed/eval_scored.jsonl. Prints AUC and thresholded precision/recall for each scorer.

How to read it:
- "host" rows cut each phish URL down to scheme+host, the fair domain-level comparison. "full" keeps the whole URL and
  lets a scorer cheat on path/length, because negatives are bare domains.
- Negatives are Tranco domains: popular sites are easy; "tail" is harder. Real traffic is harder than both.
- Small sample (about 300 phish): differences of a few points are noise.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_THRESHOLDS = (30, 60)  # suspicious+, high risk+
MODEL_THRESHOLD = 0.5


def auc(pos: list[float], neg: list[float]) -> float:
    """Probability a random phish scores above a random good domain (ties count half)."""
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def rates(pos: list[float], neg: list[float], thr: float) -> tuple[float, float]:
    recall = sum(p >= thr for p in pos) / len(pos)
    fpr = sum(n >= thr for n in neg) / len(neg)
    return recall, fpr


def blend(r: dict, key: str) -> float:
    return (r["rule_score"] / 100 + r[key]) / 2  # plain average, a baseline only (the OR layer will fit this)


def main() -> None:
    rows = [json.loads(ln) for ln in (ROOT / "data" / "processed" / "eval_scored.jsonl").read_text().splitlines() if ln]
    for variant in ("host", "full"):
        for stratum in ("all negatives", "popular", "tail"):
            pos = [r for r in rows if r["label"] == 1 and r["variant"] == variant]
            neg = [r for r in rows if r["label"] == 0 and (stratum == "all negatives" or r["stratum"] == stratum)]
            print(f"\n== phish: {variant}  vs  negatives: {stratum}   (n={len(pos)} phish, {len(neg)} good)")
            print(f"{'scorer':<28}{'AUC':>7}   recall / false-alarm at threshold")
            for name, f, thr in (
                ("rules", lambda r: r["rule_score"], None),
                ("model (url as given)", lambda r: r["model_full"], MODEL_THRESHOLD),
                ("model (scheme removed)", lambda r: r["model_noscheme"], MODEL_THRESHOLD),
                ("average rules+model", lambda r: blend(r, "model_noscheme"), None),
            ):
                p, n = [f(r) for r in pos], [f(r) for r in neg]
                line = f"{name:<28}{auc(p, n):>7.3f}   "
                if name == "rules":
                    line += "   ".join(
                        f">={t}: {rates(p, n, t)[0]:.0%} / {rates(p, n, t)[1]:.1%}" for t in RULE_THRESHOLDS
                    )
                elif thr is not None:
                    rc, fp = rates(p, n, thr)
                    line += f">={thr}: {rc:.0%} / {fp:.1%}"
                print(line)


if __name__ == "__main__":
    main()
