import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import scan as scan_ep
from app.core import auth
from app.main import app
from app.repositories import user_repo


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_AUTH", "1")
    monkeypatch.setenv("FRAUDSHIELD_RATE_LIMIT", "1")
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "s")
    scan_ep.scan_limiter.reset()
    scan_ep.deep_limiter.reset()
    user_repo.upsert("ana", auth.hash_password("correct-horse-1"), "analyst")
    yield TestClient(app)
    scan_ep.scan_limiter.reset()
    scan_ep.deep_limiter.reset()


def scan(c, deep=False):
    return c.post("/api/v1/scan", json={"url": "https://example.org/", "deep": deep})


def test_visitors_cannot_trigger_a_deep_scan(client):
    r = scan(client, deep=True)
    assert r.status_code == 401 and "staff" in r.json()["detail"]
    assert scan(client).status_code == 200  # a normal check stays public


def test_staff_may_request_a_deep_scan(client, monkeypatch):
    client.post("/api/v1/auth/login", json={"username": "ana", "password": "correct-horse-1"})
    monkeypatch.setattr("app.api.v1.endpoints.scan.scan_url", lambda url, deep=False: {
        "scan_id": "x", "state": "complete", "url": url, "score": 0, "band": "safe", "action": "allow", "confidence": 1.0,
        "reasons": [], "analyzers_ok": [], "analyzers_failed": [], "features": {}})
    assert scan(client, deep=True).status_code == 200


def test_normal_scans_are_rate_limited(client):
    for _ in range(60):
        assert scan(client).status_code == 200
    r = scan(client)
    assert r.status_code == 429 and "wait" in r.json()["detail"]


def test_deep_scans_have_a_tighter_limit(client, monkeypatch):
    client.post("/api/v1/auth/login", json={"username": "ana", "password": "correct-horse-1"})
    monkeypatch.setattr("app.api.v1.endpoints.scan.scan_url", lambda url, deep=False: {
        "scan_id": "x", "state": "complete", "url": url, "score": 0, "band": "safe", "action": "allow", "confidence": 1.0,
        "reasons": [], "analyzers_ok": [], "analyzers_failed": [], "features": {}})
    for _ in range(5):
        assert scan(client, deep=True).status_code == 200
    assert scan(client, deep=True).status_code == 429
    assert scan(client).status_code == 200  # normal scans are not affected by the deep limit


def test_limits_can_be_switched_off(client, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_RATE_LIMIT", "0")
    for _ in range(70):
        assert scan(client).status_code == 200
