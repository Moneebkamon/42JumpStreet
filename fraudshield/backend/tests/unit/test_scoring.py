import pytest
from fastapi.testclient import TestClient

from app.analyzers.brand_detector.name_matcher import brand_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.engine.pipeline import run_pipeline
from app.engine.scoring.bands import band_for
from app.engine.scoring.combiner import combine
from app.engine.scoring.overrides import apply_overrides
from app.main import app


def brand(url):
    return brand_features(normalize(url))


# ---- brand matching ----
def test_official_domain_is_not_impersonation():
    for url in ("https://www.adcb.com", "https://online.adcb.com/login", "https://tamm.abudhabi"):
        f = brand(url)
        assert f["brand_is_official"] == 1 and f["brand_impersonation"] == 0, url


def test_lookalike_domain_is_impersonation():
    f = brand("http://adcb-secure-login.top/verify")
    assert f["brand_impersonation"] == 1 and f["brand_id"] == "adcb" and f["brand_in_domain"] == 1


def test_brand_in_subdomain_of_other_site():
    f = brand("https://adcb.com.evil-site.top/login")
    assert f["brand_impersonation"] == 1 and f["brand_in_subdomain"] == 1


def test_leet_digits_still_match_brand():
    # 1 -> l, so "sa1ik" reads as "salik"; 3 -> e
    assert brand("http://sa1ik-recharge.com")["brand_id"] == "salik"
    assert brand("http://etisa1at-bill.com")["brand_id"] == "etisalat"


def test_typosquat_one_edit_picks_the_specific_brand():
    f = brand("http://emiratesnbs.com")  # one letter off "emiratesnbd"
    assert f["brand_id"] == "enbd" and f["brand_typosquat"] == 1


def test_substring_match_is_not_flagged_as_typo():
    f = brand("http://etisalatt.com")
    assert f["brand_id"] == "etisalat" and f["brand_typosquat"] == 0


def test_short_tokens_do_not_match_inside_words():
    assert brand("https://dubai-shopping.com")["brand_match"] == 0  # "du" must not match "dubai"
    assert brand("https://team-sports.com")["brand_match"] == 0  # "tamm" must not match "team"
    assert brand("https://du-recharge.com")["brand_id"] == "du"


def test_unrelated_site_has_no_brand():
    assert brand("https://www.wikipedia.org")["brand_match"] == 0


# ---- scoring ----
def test_official_site_scores_safe():
    r = run_pipeline("https://www.adcb.com/personal/login")
    assert r["band"] == "safe" and r["score"] <= 10
    assert any("official domain" in x["reason"] for x in r["reasons"])


def test_obvious_phish_scores_high_with_reasons():
    r = run_pipeline("http://adcb-secure-login.top/verify")
    assert r["score"] >= 60 and r["band"] in ("high_risk", "likely_fraud")
    rules = {x["rule"] for x in r["reasons"]}
    assert {"brand_name_not_official_domain", "risky_tld", "suspicious_keywords_2_plus"} <= rules


def test_neutral_site_scores_safe():
    r = run_pipeline("https://www.wikipedia.org/wiki/Abu_Dhabi")
    assert r["band"] == "safe"


def test_rules_for_missing_features_do_not_fire():
    r = run_pipeline("http://adcb-secure-login.top/verify")
    fired = {x["rule"] for x in r["reasons"]}
    assert "domain_age_under_7_days" not in fired and "brand_plus_credential_form" not in fired


def test_score_is_capped_at_100():
    assert combine(250) == 100 and combine(-5) == 0


def test_combine_blends_ml_when_present():
    assert combine(50, ml_score=100) == 70


def test_threat_feed_floor_and_official_cap():
    assert apply_overrides(20, {"threat_listed": 1})[0] == 85
    assert apply_overrides(90, {"brand_is_official": 1, "brand_name": "X"})[0] == 10


@pytest.mark.parametrize("score,name", [(0, "safe"), (29, "safe"), (30, "suspicious"), (60, "high_risk"), (100, "likely_fraud")])
def test_bands(score, name):
    assert band_for(score)["name"] == name


# ---- API ----
def test_scan_endpoint():
    client = TestClient(app)
    r = client.post("/api/v1/scan", json={"url": "http://adcb-secure-login.top/verify"})
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "complete" and body["score"] >= 60 and body["reasons"] and body["scan_id"]


def test_scan_endpoint_rejects_bad_url():
    client = TestClient(app)
    assert client.post("/api/v1/scan", json={"url": "http://"}).status_code == 422
    assert client.post("/api/v1/scan", json={}).status_code == 422
