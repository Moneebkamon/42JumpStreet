"""Step 2 of 3 (run with the ML venv). Add the ready model's phishing probability to the test set.

Local files only: loads ml/artifacts/urlbert-tiny-v2 (safetensors, hash-checked) through ml/tiny_bert.py. No network, no
pages opened. The model reads URL text, so we try it two ways: the URL as given, and with the scheme removed.

Run from the repo root:  ml/.venv/Scripts/python ml/score_with_model.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))

from tiny_bert import TinyBertClassifier  # noqa: E402

MODEL = ROOT / "ml" / "artifacts" / "urlbert-tiny-v2"
IN = ROOT / "data" / "processed" / "eval_set.jsonl"
OUT = ROOT / "data" / "processed" / "eval_scored.jsonl"


def strip_scheme(url: str) -> str:
    return url.split("://", 1)[-1]


def main() -> None:
    clf = TinyBertClassifier(MODEL)
    rows = [json.loads(ln) for ln in IN.read_text(encoding="utf-8").splitlines() if ln.strip()]
    urls = [r["url"] for r in rows]
    for r, p in zip(rows, clf.phish_probability(urls)):
        r["model_full"] = round(p, 5)
    for r, p in zip(rows, clf.phish_probability([strip_scheme(u) for u in urls])):
        r["model_noscheme"] = round(p, 5)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"scored {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
