"""Does the host resolve, and to how many addresses? Keys start with domain_.

domain_resolves: 1 = resolves, 0 = definitely does not exist, None = unknown (timeout / error).
"""
import socket
from concurrent.futures import ThreadPoolExecutor

from app.analyzers.domain_intel.intel_cache import FAILURE_TTL, cache


def _resolve(host: str) -> set[str]:
    return {info[4][0] for info in socket.getaddrinfo(host, None)}


def dns_features(host: str, timeout: float = 3.0) -> dict:
    key = ("dns", host)
    hit, value = cache.get(key)
    if hit:
        return value

    ttl = 3600
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        ips = pool.submit(_resolve, host).result(timeout=timeout)
        value = {"domain_resolves": int(bool(ips)), "domain_num_ips": len(ips)}
    except socket.gaierror:
        value = {"domain_resolves": 0, "domain_num_ips": 0}
    except Exception:
        value = {"domain_resolves": None, "domain_num_ips": None}
        ttl = FAILURE_TTL
    finally:
        pool.shutdown(wait=False)
    cache.set(key, value, ttl=ttl)
    return value
