"""Domain registration age and registrar via RDAP. Keys start with domain_.

Only the registered domain name is sent to rdap.org (no path, query or page data).
On any failure the age is None ("unknown"), never an exception.
"""
from datetime import datetime, timezone

import httpx

from app.analyzers.domain_intel.intel_cache import FAILURE_TTL, cache

RDAP_URL = "https://rdap.org/domain/{domain}"
UNKNOWN = {"domain_age_days": None, "domain_registrar": ""}


def parse_rdap(data: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    created = next(
        (ev.get("eventDate") for ev in data.get("events", []) if ev.get("eventAction") == "registration"), None
    )
    age = None
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = max(0, (now - dt).days)
        except ValueError:
            pass

    registrar = ""
    for ent in data.get("entities", []):
        if "registrar" in ent.get("roles", []):
            for item in (ent.get("vcardArray") or [None, []])[1]:
                if item and item[0] == "fn":
                    registrar = item[3]
    return {"domain_age_days": age, "domain_registrar": registrar}


def rdap_features(domain: str, timeout: float = 5.0) -> dict:
    key = ("rdap", domain)
    hit, value = cache.get(key)
    if hit:
        return value
    try:
        resp = httpx.get(
            RDAP_URL.format(domain=domain), timeout=timeout, follow_redirects=True,
            headers={"Accept": "application/rdap+json"},
        )
        resp.raise_for_status()
        value = parse_rdap(resp.json())
        cache.set(key, value, ttl=FAILURE_TTL if value["domain_age_days"] is None else 3600)
    except Exception:
        value = dict(UNKNOWN)
        cache.set(key, value, ttl=FAILURE_TTL)
    return value
