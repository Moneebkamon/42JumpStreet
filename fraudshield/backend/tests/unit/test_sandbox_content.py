from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.analyzers.brand_detector.name_matcher import page_brand_features
from app.analyzers.content_analyzer.contact_extractor import contact_features, extract_contacts
from app.analyzers.content_analyzer.form_inspector import form_features
from app.analyzers.content_analyzer.page_doc import build_page_doc
from app.analyzers.content_analyzer.resource_ratio import resource_features
from app.analyzers.content_analyzer.text_signals import text_features
from app.analyzers.redirect_tracer.tracer import redirect_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.engine import feature_assembler
from app.engine.pipeline import run_pipeline
from app.main import app
from app.sandbox import fetcher
from app.sandbox.policies import SandboxError, is_public_url
from app.sandbox.snapshot import PageSnapshot

STAGED = Path(__file__).resolve().parents[3] / "data" / "samples" / "staged"


def snapshot(name: str, url: str, chain=None) -> PageSnapshot:
    html = (STAGED / name).read_text(encoding="utf-8")
    return PageSnapshot(requested_url=url, final_url=url, status=200, title="", html=html,
                        redirect_chain=tuple(chain or [url]))


def doc(name: str, url: str):
    return build_page_doc(snapshot(name, url), normalize(url))


LOOKALIKE = "http://secure-portal-login.top/"
INVEST = "http://cryptogain.example/"
BENIGN = "https://sunrise-bakery.example/login"
BLOG = "https://travel-diary.example/"


# ---- content analyzers on the staged pages ----
def test_lookalike_login_form_features():
    d = doc("lookalike_bank_login.html", LOOKALIKE)
    f = form_features(d, normalize(LOOKALIKE))
    assert f["content_has_credential_form"] == 1
    assert f["content_form_cross_domain"] == 1  # posts to collector.evil-host.test


def test_benign_login_is_not_cross_domain():
    d = doc("benign_login.html", BENIGN)
    f = form_features(d, normalize(BENIGN))
    assert f["content_has_credential_form"] == 1
    assert f["content_form_cross_domain"] == 0  # the search form posts elsewhere but has no password
    assert f["content_num_forms"] == 2


def test_urgency_needs_two_distinct_phrases():
    bad = text_features(doc("lookalike_bank_login.html", LOOKALIKE), normalize(LOOKALIKE))
    ok = text_features(doc("benign_login.html", BENIGN), normalize(BENIGN))
    assert bad["content_urgency_terms"] >= 2
    assert ok["content_urgency_terms"] == 1  # "act now" alone


def test_investment_page_signals():
    n = normalize(INVEST)
    d = doc("investment_scam.html", INVEST)
    assert text_features(d, n)["content_guaranteed_return_terms"] >= 2
    r = resource_features(d, n)
    assert r["content_hidden_iframes"] == 1 and r["content_obfuscated_scripts"] == 1
    assert r["content_external_resource_ratio"] == 1.0
    c = extract_contacts(d)
    assert c["wallets"] == ["bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"]
    assert set(c["handles"]) == {"971501234567", "fake_manager_demo"}
    assert contact_features(d, n)["content_num_wallets"] == 1


def test_phone_extraction_normalizes_spacing():
    c = extract_contacts(doc("lookalike_bank_login.html", LOOKALIKE))
    assert c["phones"] == ["+971501234567"]


def test_page_claims_brand_from_title_and_heading():
    f = page_brand_features(doc("lookalike_bank_login.html", LOOKALIKE), normalize(LOOKALIKE))
    assert f["brand_page_claim"] == 1 and f["brand_page_id"] == "adcb"


def test_unrelated_page_makes_no_brand_claim():
    f = page_brand_features(doc("benign_login.html", BENIGN), normalize(BENIGN))
    assert f["brand_page_claim"] == 0


def test_redirect_features():
    chain = ["http://bit.ly/x", "http://evil.top/a", "http://evil.top/b", "http://evil.top/login"]
    s = PageSnapshot("http://bit.ly/x", chain[-1], 200, "", "<html></html>", tuple(chain))
    d = build_page_doc(s, normalize("http://bit.ly/x"))
    f = redirect_features(d, normalize("http://bit.ly/x"))
    assert f == {"redirect_hops": 3, "redirect_cross_domain": 1, "redirect_via_shortener": 1}


# ---- full pipeline with the sandbox fetch mocked ----
def fake_fetch(name):
    return lambda url: snapshot(name, url)


def test_deep_scan_of_lookalike_login_is_likely_fraud(monkeypatch):
    monkeypatch.setattr(feature_assembler, "fetch_page", fake_fetch("lookalike_bank_login.html"))
    r = run_pipeline(LOOKALIKE, deep=True)
    rules = {x["rule"] for x in r["reasons"]}
    # the domain has no brand word in it: the page claim + login form is what catches it
    assert "brand_name_not_official_domain" not in rules
    assert {"brand_plus_credential_form", "form_posts_to_other_domain", "urgency_language"} <= rules
    assert r["score"] >= 80 and r["band"] == "likely_fraud"
    assert r["page"]["contacts"]["phones"] == ["+971501234567"]
    assert "sandbox" in r["analyzers_ok"]


def test_deep_scan_of_investment_page(monkeypatch):
    monkeypatch.setattr(feature_assembler, "fetch_page", fake_fetch("investment_scam.html"))
    r = run_pipeline(INVEST, deep=True)
    rules = {x["rule"] for x in r["reasons"]}
    assert {"guaranteed_returns", "hidden_content"} <= rules
    assert r["band"] == "suspicious"


def test_deep_scan_of_benign_login_stays_safe(monkeypatch):
    monkeypatch.setattr(feature_assembler, "fetch_page", fake_fetch("benign_login.html"))
    r = run_pipeline(BENIGN, deep=True)
    assert r["band"] == "safe" and r["reasons"] == []


def test_blog_mentioning_emirates_stays_safe_without_a_form(monkeypatch):
    monkeypatch.setattr(feature_assembler, "fetch_page", fake_fetch("plain_blog.html"))
    r = run_pipeline(BLOG, deep=True)
    # the page "claims" Emirates in its title, but nothing asks for credentials, so no rule fires
    assert r["features"]["brand_page_claim"] == 1
    assert r["band"] == "safe"


def test_sandbox_failure_is_recorded_not_raised(monkeypatch):
    def boom(url):
        raise SandboxError("timed out")

    monkeypatch.setattr(feature_assembler, "fetch_page", boom)
    r = run_pipeline(LOOKALIKE, deep=True)
    assert "sandbox" in r["analyzers_failed"] and r["page"] is None
    assert r["confidence"] < 1.0
    assert r["score"] > 0  # the URL-only signals still count


def test_official_domain_never_reaches_the_sandbox(monkeypatch):
    def must_not_run(url):
        raise AssertionError("sandbox fetched an official domain")

    monkeypatch.setattr(feature_assembler, "fetch_page", must_not_run)
    r = run_pipeline("https://www.adcb.com/login", deep=True)
    assert r["band"] == "safe" and r["analyzers_failed"] == []


def test_deep_is_off_by_default():
    r = run_pipeline(LOOKALIKE)
    assert r["page"] is None and "sandbox" not in r["analyzers_ok"] + r["analyzers_failed"]


def test_api_accepts_deep(monkeypatch):
    monkeypatch.setattr(feature_assembler, "fetch_page", fake_fetch("lookalike_bank_login.html"))
    body = TestClient(app).post("/api/v1/scan", json={"url": LOOKALIKE, "deep": True}).json()
    assert body["page"]["title"].startswith("ADCB") and body["band"] == "likely_fraud"


# ---- the "public addresses only" guard ----
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/", "http://localhost/", "http://[::1]/", "http://10.0.0.5/", "http://192.168.1.1/admin",
        "http://172.16.0.9/", "http://169.254.169.254/latest/meta-data/", "http://100.64.0.1/",
        "file:///etc/passwd", "ftp://example.com/", "javascript:alert(1)", "http://", "not a url",
    ],
)
def test_private_and_non_web_addresses_are_blocked(url):
    assert is_public_url(url) is False


def test_public_ip_literal_and_no_network_schemes_are_allowed():
    assert is_public_url("http://93.184.216.34/") is True
    assert is_public_url("data:text/html,hi") is True


def test_local_allowlist_is_opt_in(monkeypatch):
    assert is_public_url("http://localhost:9000/") is False
    monkeypatch.setenv("FRAUDSHIELD_SANDBOX_ALLOW_HOSTS", "localhost, 127.0.0.1")
    assert is_public_url("http://localhost:9000/") is True
    assert is_public_url("http://10.0.0.5/") is False  # only the listed hosts


def test_fetch_page_refuses_private_targets_before_touching_a_browser():
    with pytest.raises(SandboxError, match="blocked"):
        fetcher.fetch_page("http://169.254.169.254/latest/meta-data/")
