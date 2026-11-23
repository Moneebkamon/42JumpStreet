"""Loads the brand registry from config/brands.yaml."""
import re
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import load_config


@dataclass(frozen=True)
class Brand:
    id: str
    name_en: str
    name_ar: str
    category: str
    official_domains: tuple[str, ...]
    tokens: tuple[str, ...]  # lowercase names a scammer would put in a domain
    exact_only: tuple[str, ...] = ()  # tokens that match only as a whole word (no substring), for common words
    ignore_words: tuple[str, ...] = ()  # real words that merely look like a token ("finance" is not a typo of "binance")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


@lru_cache(maxsize=1)
def get_brands() -> tuple[Brand, ...]:
    brands = []
    for b in load_config("brands").get("brands", []):
        official = tuple(d.lower() for d in b.get("official_domains", []))
        if b.get("tokens"):  # explicit list: do not derive tokens from official domains (avoids generic words)
            tokens = {t.lower() for t in b["tokens"]}
        else:
            tokens = {b["id"].lower(), _slug(b.get("name_en", ""))}
            tokens.update(d.split(".")[0] for d in official)
        tokens.discard("")
        brands.append(
            Brand(
                id=b["id"], name_en=b.get("name_en", b["id"]), name_ar=b.get("name_ar", ""),
                category=b.get("category", ""), official_domains=official, tokens=tuple(sorted(tokens)),
                exact_only=tuple(t.lower() for t in b.get("exact_only", [])),
                ignore_words=tuple(t.lower() for t in b.get("ignore_words", [])),
            )
        )
    return tuple(brands)
