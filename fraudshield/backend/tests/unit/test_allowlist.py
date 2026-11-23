import pytest
from fastapi.testclient import TestClient

from app.analyzers.threat_intel import feed_loader
from app.engine.pipeline import run_pipeline
from app.main import app

BAD = "http://adcb-secure-login.example.com/verify"  # reserved example domain; nothing real is contacted


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(tmp_path / "d.db"))
    monkeypatch.setenv("FRAUDSHIELD_THREAT_DB", str(tmp_path / "t.db"))
    return TestClient(app)


def flagged_safe(c, url=BAD):
    sid = c.post("/api/v1/scan", json={"url": url}).json()["scan_id"]
    c.post(f"/api/v1/scan/{sid}/feedback", json={"label": "safe"})
    return sid


def test_queue_lists_flagged_links_marked_safe(client):
    sid = flagged_safe(client)
    other = client.post("/api/v1/scan", json={"url": BAD}).json()["scan_id"]  # flagged, but nobody said safe
    client.post("/api/v1/scan/" + client.post("/api/v1/scan", json={"url": "https://example.org/"}).json()["scan_id"] + "/feedback", json={"label": "safe"})  # not flagged
    q = client.get("/api/v1/admin/feedback").json()
    assert [i["scan_id"] for i in q] == [sid] and other not in [i["scan_id"] for i in q]
    assert q[0]["shared_hosting"] is False and q[0]["already_allowlisted"] is False


def test_promote_lowers_the_score_and_is_audited(client):
    sid = flagged_safe(client)
    before = run_pipeline(BAD)
    assert before["score"] >= 30
    r = client.post(f"/api/v1/admin/feedback/{sid}/promote", json={"reason": "owner confirmed this is their test domain"})
    assert r.status_code == 200 and r.json()["host"] == "adcb-secure-login.example.com"
    after = run_pipeline(BAD)
    assert after["score"] <= 10 and after["band"] == "safe"
    assert any("allowlisted" in x["reason"] for x in after["reasons"])
    assert client.get("/api/v1/admin/feedback").json() == []  # reviewed, off the queue
    assert client.get("/api/v1/admin/allowlist").json()[0]["host"] == "adcb-secure-login.example.com"
    assert "allowlist.add" in [a["action"] for a in client.get("/api/v1/audit").json()]
    # an allowlisted host is re-scored, never answered from an old pre-warmed result
    assert client.post("/api/v1/scan", json={"url": BAD}).json()["band"] == "safe"


def test_removing_from_the_allowlist_restores_the_score(client):
    sid = flagged_safe(client)
    client.post(f"/api/v1/admin/feedback/{sid}/promote", json={"reason": "reviewed ok"})
    assert client.delete("/api/v1/admin/allowlist/adcb-secure-login.example.com", params={"reason": "mistake"}).status_code == 200
    assert run_pipeline(BAD)["score"] >= 30
    assert client.delete("/api/v1/admin/allowlist/adcb-secure-login.example.com").status_code == 404


def test_dismiss_keeps_the_domain_flagged(client):
    sid = flagged_safe(client)
    assert client.post(f"/api/v1/admin/feedback/{sid}/dismiss", json={"reason": "reporter was wrong"}).status_code == 200
    assert client.get("/api/v1/admin/feedback").json() == []
    assert client.get("/api/v1/admin/allowlist").json() == []
    assert run_pipeline(BAD)["score"] >= 30


def test_guard_rails(client):
    # shared hosting can never be allowlisted
    sid = flagged_safe(client, "http://adcb-secure-login.github.io/verify")
    r = client.post(f"/api/v1/admin/feedback/{sid}/promote", json={"reason": "looks fine to me"})
    assert r.status_code == 422 and "shared hosting" in r.json()["detail"]
    # only scans a person marked safe can be promoted
    unmarked = client.post("/api/v1/scan", json={"url": BAD}).json()["scan_id"]
    assert client.post(f"/api/v1/admin/feedback/{unmarked}/promote", json={"reason": "no feedback given"}).status_code == 409
    assert client.post("/api/v1/admin/feedback/nope/promote", json={"reason": "does not exist"}).status_code == 404
    assert client.post(f"/api/v1/admin/feedback/{sid}/promote", json={"reason": ""}).status_code == 422


def test_threat_listed_domains_cannot_be_allowlisted(client, tmp_path):
    sid = flagged_safe(client)
    feed_loader.load_urls("openphish", [BAD], path=tmp_path / "t.db")
    r = client.post(f"/api/v1/admin/feedback/{sid}/promote", json={"reason": "user insists it is fine"})
    assert r.status_code == 409 and "threat feed" in r.json()["detail"]


def test_a_threat_feed_hit_still_beats_the_allowlist():
    from app.engine.scoring.overrides import apply_overrides
    score, notes = apply_overrides(50, {"allowlisted": 1, "threat_listed": 1})
    assert score >= 85 and any("threat feed" in n for n in notes)
