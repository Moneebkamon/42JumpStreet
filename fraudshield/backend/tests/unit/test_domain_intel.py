from datetime import datetime, timezone

import pytest

from app.analyzers.domain_intel import dns_client, rdap_client, tls_client
from app.analyzers.domain_intel.intel_cache import IntelCache, cache
from app.analyzers.domain_intel.lookup import domain_intel_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.engine import feature_assembler
from app.engine.pipeline import run_pipeline

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)  # 2 days 2 hours after the sample registration


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_parse_rdap_age_and_registrar():
    data = {
        "events": [{"eventAction": "registration", "eventDate": "2026-11-20T10:00:00Z"}],
        "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "Namecheap"]]]}],
    }
    r = rdap_client.parse_rdap(data, now=NOW)
    assert r == {"domain_age_days": 2, "domain_registrar": "Namecheap"}


def test_parse_rdap_missing_or_bad_date_is_unknown():
    assert rdap_client.parse_rdap({}, now=NOW)["domain_age_days"] is None
    assert rdap_client.parse_rdap({"events": [{"eventAction": "registration", "eventDate": "garbage"}]}, now=NOW)["domain_age_days"] is None


def test_rdap_failure_returns_unknown_and_never_raises(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(rdap_client.httpx, "get", boom)
    assert rdap_client.rdap_features("example.com") == {"domain_age_days": None, "domain_registrar": ""}


def test_rdap_result_is_cached(monkeypatch):
    calls = []

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"events": [{"eventAction": "registration", "eventDate": "2020-01-01T00:00:00Z"}]}

    monkeypatch.setattr(rdap_client.httpx, "get", lambda *a, **k: calls.append(1) or Resp())
    first = rdap_client.rdap_features("example.com")
    second = rdap_client.rdap_features("example.com")
    assert first == second and len(calls) == 1 and first["domain_age_days"] > 365


def test_dns_nxdomain_vs_unknown(monkeypatch):
    import socket

    def nx(host):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(dns_client, "_resolve", nx)
    assert dns_client.dns_features("nope.invalid")["domain_resolves"] == 0

    cache.clear()

    def other(host):
        raise RuntimeError("resolver crashed")

    monkeypatch.setattr(dns_client, "_resolve", other)
    assert dns_client.dns_features("x.example")["domain_resolves"] is None


def test_tls_unreachable_is_reported_not_raised(monkeypatch):
    def refuse(*a, **k):
        raise ConnectionRefusedError()

    monkeypatch.setattr(tls_client.socket, "create_connection", refuse)
    r = tls_client.tls_features("example.com")
    assert r["tls_available"] == 0 and r["tls_cert_age_days"] is None


def test_lookup_merges_and_survives_a_failing_client(monkeypatch):
    import app.analyzers.domain_intel.lookup as lk

    monkeypatch.setattr(lk, "rdap_features", lambda d: {"domain_age_days": 3, "domain_registrar": "R"})
    monkeypatch.setattr(lk, "dns_features", lambda h: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(lk, "tls_features", lambda h: {"tls_available": 1, "tls_valid": 1, "tls_cert_age_days": 1, "tls_issuer": "CA"})
    f = domain_intel_features(normalize("https://evil-example.top"))
    assert f["domain_age_days"] == 3 and f["tls_cert_age_days"] == 1
    assert f["domain_resolves"] is None  # failed client -> explicit unknown


def test_cache_expires():
    c = IntelCache()
    c.set("k", 1, ttl=-1)
    assert c.get("k") == (False, None)


def test_new_domain_and_new_cert_raise_the_score(monkeypatch):
    monkeypatch.setattr(
        feature_assembler, "domain_intel_features",
        lambda n: {"domain_age_days": 2, "tls_cert_age_days": 1, "tls_available": 1, "tls_valid": 1},
    )
    monkeypatch.setitem(feature_assembler.NETWORK_ANALYZERS, "domain_intel", feature_assembler.domain_intel_features)
    base = run_pipeline("http://adcb-secure-login.top/verify", use_network=False)
    deep = run_pipeline("http://adcb-secure-login.top/verify", use_network=True)
    assert deep["score"] > base["score"]
    rules = {r["rule"] for r in deep["reasons"]}
    assert {"domain_age_under_7_days", "very_new_certificate"} <= rules


def test_official_domain_shows_lookups_but_stays_safe(monkeypatch):
    """The age and certificate facts are shown for an official domain, but even a "brand new" answer cannot flag it."""
    monkeypatch.setitem(
        feature_assembler.NETWORK_ANALYZERS, "domain_intel",
        lambda n: {"domain_age_days": 2, "tls_cert_age_days": 1, "tls_available": 1, "tls_valid": 1},
    )
    r = run_pipeline("https://www.adcb.com", use_network=True)
    assert r["band"] == "safe" and r["analyzers_failed"] == []
    assert r["features"]["domain_age_days"] == 2 and r["features"]["tls_cert_age_days"] == 1
    assert any("official domain" in n.lower() for n in r.get("notes", []) + [x.get("text", "") for x in r["reasons"]]) or r["score"] <= 10


def test_network_off_by_default():
    r = run_pipeline("http://adcb-secure-login.top/verify")
    assert "domain_intel" not in r["analyzers_ok"]
