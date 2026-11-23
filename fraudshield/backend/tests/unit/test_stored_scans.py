import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import scan_repo


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "s.db"))
    return TestClient(app)


def scan(c, url, **kw):
    r = c.post("/api/v1/scan", json={"url": url, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_scan_is_stored_and_fetchable(client):
    made = scan(client, "http://adcb-secure-login.top/verify")
    got = client.get(f"/api/v1/scan/{made['scan_id']}")
    assert got.status_code == 200
    body = got.json()
    assert body["score"] == made["score"] and body["reasons"] == made["reasons"]
    assert body["created_at"] and body["feedback"] is None


def test_unknown_scan_is_404(client):
    assert client.get("/api/v1/scan/nope").status_code == 404
    assert client.post("/api/v1/scan/nope/feedback", json={"label": "scam"}).status_code == 404


def test_history_newest_first_with_paging_and_filter(client):
    ids = [scan(client, u)["scan_id"] for u in ("http://adcb-secure-login.top", "https://example.org", "http://sa1ik-recharge.com")]
    hist = client.get("/api/v1/scans").json()
    assert [h["scan_id"] for h in hist] == ids[::-1]
    assert {"url", "score", "band", "deep", "cached", "created_at"} <= set(hist[0])
    assert len(client.get("/api/v1/scans?limit=1&offset=1").json()) == 1
    assert all(h["score"] >= 30 for h in client.get("/api/v1/scans?min_score=30").json())
    assert client.get("/api/v1/scans?limit=0").status_code == 422


def test_feedback_is_saved_and_validated(client):
    sid = scan(client, "http://adcb-secure-login.top")["scan_id"]
    assert client.post(f"/api/v1/scan/{sid}/feedback", json={"label": "scam"}).json()["feedback"] == "scam"
    assert client.get(f"/api/v1/scan/{sid}").json()["feedback"] == "scam"
    assert client.get("/api/v1/scans").json()[0]["feedback"] == "scam"
    assert client.post(f"/api/v1/scan/{sid}/feedback", json={"label": "maybe"}).status_code == 422
    with pytest.raises(ValueError):
        scan_repo.set_feedback(sid, "maybe")


def test_bad_url_is_not_stored(client):
    assert client.post("/api/v1/scan", json={"url": "http://"}).status_code == 422
    assert client.get("/api/v1/scans").json() == []


def test_storage_failure_does_not_break_the_scan(client, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(scan_repo, "save", boom)
    assert scan(client, "http://adcb-secure-login.top")["score"] > 0
