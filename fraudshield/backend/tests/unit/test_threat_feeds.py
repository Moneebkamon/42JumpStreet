import pytest

from app.analyzers.threat_intel import feed_loader
from app.analyzers.threat_intel.feed_loader import load_feed_text, parse_openphish, parse_phishtank, parse_urlhaus
from app.analyzers.threat_intel.feed_lookup import threat_features
from app.analyzers.url_analyzer.normalizer import normalize
from app.engine.pipeline import run_pipeline

URLHAUS = """# abuse.ch URLhaus
# id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
"1","2026-11-01 10:00:00","http://bad-bank-login.top/a/b","online","2026-11-01","malware_download","x","https://urlhaus.abuse.ch/url/1/","r"
"2","2026-11-01 10:05:00","https://evil.github.io/phish","online","2026-11-01","phishing","x","https://urlhaus.abuse.ch/url/2/","r"
"""
PHISHTANK = "phish_id,url,phish_detail_url,submission_time,verified,online\n1,http://pt-bad.xyz/login,u,t,yes,yes\n2,http://unverified.xyz/,u,t,no,yes\n"


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "t.db"
    monkeypatch.setenv("FRAUDSHIELD_THREAT_DB", str(path))
    return path


def feat(url):
    return threat_features(normalize(url))


def test_parsers():
    assert parse_openphish("# c\nhttp://a.top/x\n\n http://b.top \n") == ["http://a.top/x", "http://b.top"]
    assert parse_urlhaus(URLHAUS) == ["http://bad-bank-login.top/a/b", "https://evil.github.io/phish"]
    assert parse_phishtank(PHISHTANK) == ["http://pt-bad.xyz/login"]


def test_no_database_means_not_listed(db):
    assert feat("http://anything.top") == {"threat_listed": 0, "threat_source": ""}
    assert not db.exists()  # lookup never creates it


def test_exact_url_and_host_match(db):
    assert load_feed_text("urlhaus", URLHAUS) == 2
    assert feat("http://bad-bank-login.top/a/b")["threat_listed"] == 1
    other_page = feat("http://bad-bank-login.top/other")
    assert other_page == {"threat_listed": 1, "threat_source": "urlhaus"}  # same host, different page
    assert feat("http://clean-site.top/")["threat_listed"] == 0


def test_shared_hosting_needs_exact_url(db):
    load_feed_text("urlhaus", URLHAUS)
    assert feat("https://evil.github.io/phish")["threat_listed"] == 1
    assert feat("https://innocent.github.io/")["threat_listed"] == 0
    assert feat("https://evil.github.io/other")["threat_listed"] == 0


def test_reload_replaces_that_sources_rows_only(db):
    load_feed_text("openphish", "http://old.top/\n")
    load_feed_text("phishtank", PHISHTANK)
    load_feed_text("openphish", "http://new.top/\n")
    assert feat("http://old.top/")["threat_listed"] == 0
    assert feat("http://new.top/")["threat_source"] == "openphish"
    assert feat("http://pt-bad.xyz/login")["threat_source"] == "phishtank"


def test_unknown_source_and_bad_urls(db):
    with pytest.raises(ValueError):
        load_feed_text("nope", "x")
    assert feed_loader.load_urls("openphish", ["", "http://", "http://ok.top/"]) == 1


def test_listed_url_is_floored_by_the_override(db):
    load_feed_text("openphish", "http://plain-looking.example/\n")
    r = run_pipeline("http://plain-looking.example/")
    assert r["score"] >= 85 and r["band"] == "likely_fraud"
    assert any("threat feed" in x["reason"] for x in r["reasons"])
    assert "threat_intel" in r["analyzers_ok"]
