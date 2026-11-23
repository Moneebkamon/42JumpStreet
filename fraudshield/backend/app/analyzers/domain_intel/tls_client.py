"""Certificate presence, validity and age. Keys start with tls_.

tls_available 0 = nothing answered on 443. tls_valid 0 = answered but the certificate failed
verification (itself a warning sign). tls_cert_age_days is None when no certificate was read.
"""
import socket
import ssl
import time

import certifi

from app.analyzers.domain_intel.intel_cache import FAILURE_TTL, cache

NO_TLS = {"tls_available": 0, "tls_valid": 0, "tls_cert_age_days": None, "tls_issuer": ""}


def _cert_info(cert: dict) -> dict:
    issued = ssl.cert_time_to_seconds(cert["notBefore"])
    issuer = next((v for rdn in cert.get("issuer", ()) for k, v in rdn if k == "organizationName"), "")
    return {
        "tls_available": 1, "tls_valid": 1,
        "tls_cert_age_days": max(0, int((time.time() - issued) // 86400)), "tls_issuer": issuer,
    }


def tls_features(host: str, port: int = 443, timeout: float = 4.0) -> dict:
    key = ("tls", host, port)
    hit, value = cache.get(key)
    if hit:
        return value

    ttl = 3600
    try:
        # Verify against certifi's CA list, not the OS store: the Windows store loads roots lazily
        # and made valid sites look invalid, which would give false "bad certificate" signals.
        ctx = ssl.create_default_context(cafile=certifi.where())
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                value = _cert_info(tls.getpeercert())
    except ssl.SSLError:
        value = {**NO_TLS, "tls_available": 1}
    except OSError:
        value = dict(NO_TLS)
        ttl = FAILURE_TTL
    except Exception:
        value = dict(NO_TLS)
        ttl = FAILURE_TTL
    cache.set(key, value, ttl=ttl)
    return value
