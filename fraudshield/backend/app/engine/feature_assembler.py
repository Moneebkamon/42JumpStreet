"""Merge analyzer outputs into one flat feature dict and record which analyzers worked."""
from app.analyzers.allowlist_check import allowlist_features
from app.analyzers.brand_detector.name_matcher import brand_features, page_brand_features
from app.analyzers.content_analyzer.contact_extractor import contact_features, extract_contacts
from app.analyzers.content_analyzer.form_inspector import form_features
from app.analyzers.content_analyzer.page_doc import build_page_doc
from app.analyzers.content_analyzer.resource_ratio import resource_features
from app.analyzers.content_analyzer.text_signals import text_features
from app.analyzers.domain_intel.lookup import domain_intel_features
from app.analyzers.redirect_tracer.tracer import redirect_features
from app.analyzers.threat_intel.feed_lookup import threat_features
from app.ml.predictor import ml_features
from app.analyzers.url_analyzer.homoglyph import homoglyph_features
from app.analyzers.url_analyzer.hosting import hosting_features
from app.analyzers.url_analyzer.lexical import lexical_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.analyzers.url_analyzer.shortener import shortener_features
from app.sandbox.fetcher import fetch_page

# Offline analyzers: function(NormalizedURL) -> dict. Always run.
URL_ANALYZERS = {
    "lexical": lexical_features,
    "hosting": hosting_features,
    "homoglyph": homoglyph_features,
    "shortener": shortener_features,
    "brand": brand_features,
    "allowlist": allowlist_features,  # admin-reviewed false positives
    "threat_intel": threat_features,  # local feed database; "not listed" when no feed is loaded
    "url_model": ml_features,  # ready phishing-URL model; reports ml_available=0 when it is not installed
}

# Network analyzers: run only when use_network is True.
NETWORK_ANALYZERS = {
    "domain_intel": domain_intel_features,
}

# Content analyzers: function(PageDoc, NormalizedURL) -> dict. Run only on a deep scan, after the sandbox
# fetched the page.
CONTENT_ANALYZERS = {
    "forms": form_features,
    "text_signals": text_features,
    "resources": resource_features,
    "contacts": contact_features,
    "redirects": redirect_features,
    "page_brand": page_brand_features,
}


def assemble_features(raw_url: str, use_network: bool = False, deep: bool = False) -> dict:
    """Return {"url", "features", "analyzers_ok", "analyzers_failed", "page"}.

    Raises ValueError only when the URL itself is unusable. A failing analyzer (or a page that cannot be
    fetched) is reported in analyzers_failed instead of crashing the scan. "page" is None unless a deep
    scan fetched the page.
    """
    n = normalize(raw_url)
    features: dict = {}
    ok: list[str] = []
    failed: list[str] = []
    page: dict | None = None

    def run(analyzers: dict, *args) -> None:
        for name, fn in analyzers.items():
            try:
                features.update(fn(*args))
                ok.append(name)
            except Exception:
                failed.append(name)

    run(URL_ANALYZERS, n)
    # An official domain is capped low anyway, so skip the page fetch for it. The cheap domain lookups (age, DNS,
    # certificate) still run: they do not change the verdict, but people want to see the facts for a real domain.
    if use_network:
        run(NETWORK_ANALYZERS, n)
    if features.get("brand_is_official") != 1:
        if deep:
            try:
                doc = build_page_doc(fetch_page(n.url), n)
            except Exception:
                failed.append("sandbox")
            else:
                ok.append("sandbox")
                run(CONTENT_ANALYZERS, doc, n)
                page = {
                    "final_url": doc.snapshot.final_url,
                    "title": doc.title,
                    "status": doc.snapshot.status,
                    "redirect_chain": list(doc.snapshot.redirect_chain),
                    "network_hosts": list(doc.snapshot.network_hosts),
                    "blocked_hosts": list(doc.snapshot.blocked_hosts),
                    "contacts": extract_contacts(doc),
                    "truncated": doc.snapshot.truncated,
                }
    return {"url": n.url, "features": features, "analyzers_ok": ok, "analyzers_failed": failed, "page": page}
