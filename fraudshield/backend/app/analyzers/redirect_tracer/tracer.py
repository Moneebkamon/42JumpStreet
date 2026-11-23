"""Features from the redirect chain the sandbox recorded. Keys start with redirect_."""
from app.analyzers.content_analyzer.page_doc import PageDoc
from app.analyzers.url_analyzer.normalizer import NormalizedURL, normalize
from app.analyzers.url_analyzer.shortener import SHORTENERS


def _registered(url: str) -> str:
    try:
        return normalize(url).registered_domain
    except ValueError:
        return ""


def redirect_features(doc: PageDoc, n: NormalizedURL) -> dict:
    chain = doc.snapshot.redirect_chain or (doc.snapshot.requested_url,)
    domains = [_registered(u) for u in chain]
    return {
        "redirect_hops": max(0, len(chain) - 1),
        "redirect_cross_domain": int(bool(domains[0]) and bool(domains[-1]) and domains[0] != domains[-1]),
        "redirect_via_shortener": int(any(d in SHORTENERS for d in domains)),
    }
