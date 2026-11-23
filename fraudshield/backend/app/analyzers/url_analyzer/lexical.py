"""Cheap numeric features read straight from the URL text. Keys start with url_."""
import math
from collections import Counter

from app.analyzers.url_analyzer.normalizer import NormalizedURL
from app.core.config import load_config

SUSPICIOUS_KEYWORDS = (
    "login", "signin", "verify", "secure", "account", "update", "confirm", "bank",
    "wallet", "password", "payment", "invoice", "bonus", "free", "support", "fine",
)


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    n = len(text)
    return -sum(c / n * math.log2(c / n) for c in Counter(text).values())


def _tld_risk(suffix: str) -> float:
    cfg = load_config("tld_risk")
    tlds = cfg.get("tlds", {})
    default = float(cfg.get("default", 0.2))
    if suffix in tlds:
        return float(tlds[suffix])
    return float(tlds.get(suffix.rsplit(".", 1)[-1], default))


def lexical_features(n: NormalizedURL) -> dict:
    haystack = (n.host + n.path).lower()
    return {
        "url_length": len(n.url),
        "url_host_length": len(n.host),
        "url_path_length": len(n.path),
        "url_num_dots": n.host.count("."),
        "url_num_hyphens": n.host.count("-"),
        "url_num_digits_host": sum(ch.isdigit() for ch in n.host),
        "url_subdomain_depth": len(n.subdomain.split(".")) if n.subdomain else 0,
        "url_domain_entropy": round(_entropy(n.domain), 4),
        "url_is_ip_host": int(n.is_ip),
        "url_has_at_symbol": int("@" in n.original),
        "url_num_query_params": n.query.count("&") + 1 if n.query else 0,
        "url_is_https": int(n.scheme == "https" and not n.scheme_assumed),
        "url_suspicious_keywords": sum(kw in haystack for kw in SUSPICIOUS_KEYWORDS),
        "url_tld_risk": _tld_risk(n.suffix),
    }
