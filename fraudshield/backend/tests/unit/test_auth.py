import pytest
from fastapi.testclient import TestClient

from app.core import auth
from app.main import app
from app.repositories import user_repo

PW = "correct-horse-battery"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_AUTH", "1")
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(tmp_path / "d.db"))
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "test-secret")
    from app.api.v1.endpoints import auth as auth_ep
    auth_ep.limiter.reset()
    user_repo.upsert("ana", auth.hash_password(PW), "analyst")
    user_repo.upsert("root", auth.hash_password(PW), "admin")
    return TestClient(app)


def login(c, user="ana", pw=PW):
    return c.post("/api/v1/auth/login", json={"username": user, "password": pw})


def test_password_hash_roundtrip_and_no_plaintext():
    h = auth.hash_password(PW)
    assert PW not in h and auth.verify_password(PW, h) and not auth.verify_password("nope", h)
    assert auth.hash_password(PW) != h  # salted
    assert not auth.verify_password(PW, "garbage")


def test_token_rejects_tampering_and_expiry(monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "s")
    t = auth.make_token("ana", "analyst", now=1000)
    assert auth.read_token(t, now=1001) == ("ana", "analyst")
    assert auth.read_token(t, now=1000 + auth.SESSION_SECONDS + 5) is None
    import base64
    raw = base64.urlsafe_b64decode(t).decode().replace("analyst", "admin")
    assert auth.read_token(base64.urlsafe_b64encode(raw.encode()).decode(), now=1001) is None
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "other")
    assert auth.read_token(t, now=1001) is None


def test_staff_routes_need_login_public_routes_do_not(client):
    for path in ("/api/v1/queue", "/api/v1/cases", "/api/v1/feed", "/api/v1/stats", "/api/v1/citizen-reports"):
        assert client.get(path).status_code == 401, path
    assert client.get("/api/v1/audit").status_code == 401
    assert client.get("/api/v1/health").status_code == 200
    assert client.post("/api/v1/scan", json={"url": "https://example.org/"}).status_code == 200
    assert client.post("/api/v1/citizen-reports", json={"url": "https://example.org/x"}).status_code == 201


def test_login_logout_and_me(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert login(client, pw="wrong").status_code == 401
    assert login(client, user="nobody").status_code == 401
    r = login(client)
    assert r.status_code == 200 and r.json() == {"username": "ana", "role": "analyst"}
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/v1/auth/me").json()["username"] == "ana"
    assert client.get("/api/v1/queue").status_code == 200
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/queue").status_code == 401


def test_analyst_cannot_read_audit_admin_can(client):
    login(client)
    assert client.get("/api/v1/audit").status_code == 403
    client.post("/api/v1/auth/logout")
    login(client, user="root")
    assert client.get("/api/v1/audit").status_code == 200


def test_actor_comes_from_the_session_not_the_header(client):
    login(client)
    sid = client.post("/api/v1/scan", json={"url": "http://adcb-secure-login.example.com/verify"}).json()["scan_id"]
    r = client.post("/api/v1/cases", json={"source": "scan", "source_ref": sid}, headers={"X-Actor": "someone-else"})
    assert r.status_code == 201 and r.json()["created_by"] == "ana"
    client.post("/api/v1/auth/logout")
    login(client, user="root")
    entries = client.get("/api/v1/audit").json()
    assert ("case.create", "ana") in [(e["action"], e["actor"]) for e in entries]
    assert "auth.login" in [e["action"] for e in entries]


def test_failed_logins_are_audited_and_rate_limited(client):
    for _ in range(10):
        assert login(client, pw="bad").status_code == 401
    assert login(client, pw="bad").status_code == 429
    assert login(client).status_code == 429  # even the right password waits out the window
    from app.api.v1.endpoints import auth as auth_ep
    auth_ep.limiter.reset()
    login(client, user="root")
    assert "auth.login_failed" in [e["action"] for e in client.get("/api/v1/audit").json()]


def test_auth_off_mode_is_open(client, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_AUTH", "0")
    assert client.get("/api/v1/queue").status_code == 200
    assert client.get("/api/v1/auth/me").json()["auth_enabled"] is False
