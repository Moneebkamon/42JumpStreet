import pytest

from app.analyzers.url_analyzer.homoglyph import homoglyph_features, skeleton
from app.analyzers.url_analyzer.lexical import lexical_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.analyzers.url_analyzer.shortener import shortener_features
from app.engine.feature_assembler import assemble_features


def test_normalize_strips_tracking_and_lowercases():
    n = normalize("HTTPS://Login.Example.COM:443/Path?utm_source=x&id=7&fbclid=abc")
    assert n.host == "login.example.com"
    assert n.url == "https://login.example.com/Path?id=7"
    assert n.registered_domain == "example.com"
    assert n.subdomain == "login"
    assert n.port is None


def test_normalize_adds_scheme_and_flags_it():
    n = normalize("example.com/a")
    assert n.scheme == "https" and n.scheme_assumed is True


def test_normalize_ip_host():
    n = normalize("http://192.168.1.10/login")
    assert n.is_ip is True and n.registered_domain == "192.168.1.10"


def test_normalize_gov_ae_suffix():
    assert normalize("https://www.adpolice.gov.ae").registered_domain == "adpolice.gov.ae"


@pytest.mark.parametrize("bad", ["", "   ", "http://"])
def test_normalize_rejects_unusable(bad):
    with pytest.raises(ValueError):
        normalize(bad)


def test_lexical_keywords_and_tld_risk():
    f = lexical_features(normalize("http://secure-login-adcb.top/verify/account"))
    assert f["url_suspicious_keywords"] >= 3
    assert f["url_tld_risk"] == 0.7
    assert f["url_is_https"] == 0
    assert f["url_num_hyphens"] == 2


def test_lexical_official_domain_is_low_risk():
    f = lexical_features(normalize("https://www.adcb.com"))
    assert f["url_tld_risk"] == 0.2 and f["url_is_https"] == 1


def test_homoglyph_punycode_and_mixed_script():
    # xn--pple-43d.com is "apple.com" with a Cyrillic 'a'
    f = homoglyph_features(normalize("http://xn--pple-43d.com"))
    assert f["url_has_punycode"] == 1 and f["url_has_non_ascii"] == 1
    # first two letters Cyrillic, rest Latin
    g = homoglyph_features(normalize("http://раypal.com"))
    assert g["url_mixed_script"] == 1 and g["url_confusable_chars"] == 2


def test_homoglyph_clean_host():
    f = homoglyph_features(normalize("https://www.emiratesnbd.com"))
    assert f["url_has_punycode"] == 0 and f["url_mixed_script"] == 0


def test_skeleton_collapses_lookalikes():
    assert skeleton("paypa1.com") == skeleton("paypal.com")
    assert skeleton("rnashreq.com") == skeleton("mashreq.com")


def test_shortener():
    assert shortener_features(normalize("https://bit.ly/abc"))["url_is_shortener"] == 1
    assert shortener_features(normalize("https://adcb.com"))["url_is_shortener"] == 0


def test_assemble_reports_success():
    r = assemble_features("http://adcb-secure-login.top/verify?utm_x=1")
    assert r["analyzers_failed"] == []
    assert set(r["analyzers_ok"]) == {"lexical", "homoglyph", "shortener", "brand", "allowlist", "hosting", "threat_intel", "url_model"}
    assert r["features"]["url_tld_risk"] == 0.7
    assert "utm_x" not in r["url"]


def test_assemble_raises_on_unusable_url():
    with pytest.raises(ValueError):
        assemble_features("")
