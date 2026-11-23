"""Write a SIMULATED certificate-stream sample to data/samples/ct_stream.jsonl (offline, deterministic).

Every line is one certificate event. `label` marks what the generator planted, so the prefilter's recall
can be measured. The data is invented: it is not a real recording of any certificate log.

Run from the repo root:  backend/.venv/Scripts/python scripts/generate_ct_sample.py
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "samples" / "ct_stream.jsonl"

SEED = 42
N_BENIGN = 900
START = datetime(2026, 11, 20, 8, 0, 0, tzinfo=timezone.utc)

WORDS = (
    "blue peak studio garden coffee bakery north harbor pixel craft maple river stone cloud fox orbit "
    "lemon cedar atlas nova solar tiny happy quick green forest dental yoga photo travel kids pets "
    "furniture lighting plumbing tailor print flower bike hobby music book cinema trail summit"
).split()
BENIGN_TLDS = ["com"] * 6 + ["net", "org", "ae", "io", "co", "shop", "online", "site"]
RISKY_TLDS = ["top", "xyz", "click", "icu", "vip", "shop", "online", "site"]
KEYWORDS = ["login", "verify", "secure", "account", "wallet", "update", "confirm", "payment", "support"]
LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "l": "1", "s": "5"}
CYRILLIC = {"a": "а", "e": "е", "o": "о", "p": "р", "c": "с"}


def _leet(token: str, rng: random.Random) -> str:
    idx = [i for i, c in enumerate(token) if c in LEET]
    if not idx:
        return token
    i = rng.choice(idx)
    return token[:i] + LEET[token[i]] + token[i + 1:]


def _typo(token: str, rng: random.Random) -> str:
    if len(token) < 7:
        return _leet(token, rng)
    i = rng.randrange(1, len(token) - 1)
    return token[:i] + token[i + 1:]  # one letter dropped


def _homoglyph(token: str) -> str | None:
    swapped = "".join(CYRILLIC.get(c, c) for c in token)
    if swapped == token:
        return None
    return ("xn--" + swapped.encode("punycode").decode("ascii")) if not swapped.isascii() else None


def make_brand_domain(brand: dict, rng: random.Random) -> tuple[str, str]:
    # brand-NAME tokens only (id, name, official domain label); `keywords` also holds generic words like "login"
    names = {brand["id"], "".join(c for c in brand["name_en"].lower() if c.isalnum())}
    names |= {d.split(".")[0] for d in brand["official_domains"]}
    long_names = sorted(t for t in names if len(t) >= 3)
    token = rng.choice(long_names) if long_names else max(names, key=len)
    kw, tld = rng.choice(KEYWORDS), rng.choice(RISKY_TLDS)
    kind = rng.choice(["combo", "combo", "typo", "leet", "subdomain", "homoglyph"])
    if kind == "combo":
        return f"{token}-{kw}.{tld}", "lookalike"
    if kind == "typo":
        return f"{_typo(token, rng)}-{kw}.com", "lookalike"
    if kind == "leet":
        return f"{_leet(token, rng)}{rng.choice(['', '-' + kw])}.{tld}", "lookalike"
    if kind == "subdomain":
        official = brand["official_domains"][0]
        return f"{official}.{kw}-{rng.choice(WORDS)}.{tld}", "lookalike"
    puny = _homoglyph(token)
    return (f"{puny}.com", "homoglyph") if puny else (f"{token}-{kw}.{tld}", "lookalike")


def make_keyword_domain(rng: random.Random) -> tuple[str, str]:
    kw1, kw2 = rng.sample(KEYWORDS, 2)
    if rng.random() < 0.5:
        return f"{rng.choice(WORDS)}-{kw1}.{rng.choice(RISKY_TLDS)}", "keyword"
    return f"{kw1}-{kw2}-{rng.choice(WORDS)}.com", "keyword"


def main() -> None:
    rng = random.Random(SEED)
    brands = yaml.safe_load((ROOT / "config" / "brands.yaml").read_text(encoding="utf-8"))["brands"]

    rows: list[tuple[str, str]] = []
    for _ in range(N_BENIGN):
        name = "".join(rng.sample(WORDS, 2)) if rng.random() < 0.6 else f"{rng.choice(WORDS)}-{rng.choice(WORDS)}"
        rows.append((f"{name}{rng.choice(['', '24', '360', 'hub'])}.{rng.choice(BENIGN_TLDS)}", "benign"))
    for _ in range(60):
        rows.append(make_brand_domain(rng.choice(brands), rng))
    for _ in range(25):
        rows.append(make_keyword_domain(rng))
    for b in brands[:6]:  # real brand domains show up too; the prefilter must drop them
        rows.append((rng.choice(["www.", "online.", ""]) + b["official_domains"][0], "official"))

    rng.shuffle(rows)
    seen: set[str] = set()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t = START
    count = 0
    with OUT.open("w", encoding="utf-8") as fh:
        for domain, label in rows:
            if domain in seen:
                continue
            seen.add(domain)
            t += timedelta(seconds=rng.randint(1, 20))
            names = [domain] + ([f"www.{domain}"] if rng.random() < 0.3 and not domain.startswith("www.") else [])
            count += 1
            fh.write(json.dumps({
                "seq": count, "issued_at": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "domains": names, "label": label, "simulated": True,
            }, ensure_ascii=True) + "\n")
    print(f"wrote {count} events to {OUT}")


if __name__ == "__main__":
    main()
