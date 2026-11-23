"""Cheap first cut over newly issued certificate domains. It only picks candidates; the scoring engine decides.

A domain is kept when at least one of these holds (official brand domains are always dropped):
- brand:<id>        it uses a protected brand's name (incl. leet digits and one-letter typos)
- homoglyph         punycode, non-ASCII or mixed-script characters
- keyword_risky_tld a sensitive word (login, verify, wallet...) on a risky TLD (tld_risk >= 0.5)
- keyword_hyphens   a sensitive word in a name with 2+ hyphens ("secure-account-update.com")
"""
from dataclasses import dataclass, field

from app.analyzers.brand_detector.name_matcher import find_brand_match
from app.analyzers.brand_detector.ownership_check import official_brand
from app.analyzers.url_analyzer.homoglyph import homoglyph_features
from app.analyzers.url_analyzer.lexical import lexical_features
from app.analyzers.url_analyzer.normalizer import normalize

RISKY_TLD = 0.5
MANY_HYPHENS = 2


@dataclass(frozen=True)
class PrefilterResult:
    domain: str
    keep: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


def clean_domain(raw: str) -> str:
    """Certificates list names like '*.example.com'; drop the wildcard and trailing dot."""
    d = raw.strip().lower().rstrip(".")
    while d.startswith("*."):
        d = d[2:]
    return d


def prefilter(raw_domain: str) -> PrefilterResult:
    domain = clean_domain(raw_domain)
    try:
        n = normalize(domain)
    except ValueError:
        return PrefilterResult(domain, False)
    if n.is_ip or not n.suffix or official_brand(n.host):
        return PrefilterResult(domain, False)

    reasons: list[str] = []
    m = find_brand_match(n)
    if m:
        reasons.append(f"brand:{m.brand.id}")

    h = homoglyph_features(n)
    if h["url_has_punycode"] or h["url_has_non_ascii"] or h["url_mixed_script"]:
        reasons.append("homoglyph")

    lex = lexical_features(n)
    if lex["url_suspicious_keywords"]:
        if lex["url_tld_risk"] >= RISKY_TLD:
            reasons.append("keyword_risky_tld")
        if lex["url_num_hyphens"] >= MANY_HYPHENS:
            reasons.append("keyword_hyphens")

    return PrefilterResult(domain, bool(reasons), tuple(reasons))
