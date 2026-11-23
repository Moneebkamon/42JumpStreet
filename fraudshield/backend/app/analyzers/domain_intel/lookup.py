"""Run the RDAP, DNS and TLS lookups in parallel and merge them into one feature dict."""
from concurrent.futures import ThreadPoolExecutor

from app.analyzers.domain_intel.dns_client import dns_features
from app.analyzers.domain_intel.rdap_client import UNKNOWN as RDAP_UNKNOWN
from app.analyzers.domain_intel.rdap_client import rdap_features
from app.analyzers.domain_intel.tls_client import NO_TLS, tls_features
from app.analyzers.url_analyzer.normalizer import NormalizedURL

OVERALL_TIMEOUT = 7.0


def domain_intel_features(n: NormalizedURL) -> dict:
    """Never raises: a lookup that fails or times out contributes its 'unknown' values."""
    if n.is_ip:
        return {**RDAP_UNKNOWN, **dns_features(n.host), **NO_TLS}

    pool = ThreadPoolExecutor(max_workers=3)
    futures = {
        "rdap": (pool.submit(rdap_features, n.registered_domain), RDAP_UNKNOWN),
        "dns": (pool.submit(dns_features, n.host), {"domain_resolves": None, "domain_num_ips": None}),
        "tls": (pool.submit(tls_features, n.host), NO_TLS),
    }
    merged: dict = {}
    try:
        for fut, fallback in futures.values():
            try:
                merged.update(fut.result(timeout=OVERALL_TIMEOUT))
            except Exception:
                merged.update(fallback)
    finally:
        pool.shutdown(wait=False)
    return merged
