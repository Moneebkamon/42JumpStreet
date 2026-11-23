"""Recognize known URL shorteners. Keys start with url_."""
from app.analyzers.url_analyzer.normalizer import NormalizedURL

SHORTENERS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly",
    "cutt.ly", "shorturl.at", "tiny.cc", "rb.gy", "t.ly", "s.id", "lnkd.in", "bit.do", "v.gd",
})


def shortener_features(n: NormalizedURL) -> dict:
    return {"url_is_shortener": int(n.registered_domain in SHORTENERS or n.host in SHORTENERS)}
