"""Public accounts, role gating, per-user data, the message guard, webhooks and the extension device token.
All offline: scoring is stubbed where a specific band is needed, mail goes to a temp outbox."""
import pytest
from fastapi.testclient import TestClient

from app.core import auth
from app.guard.link_extractor import extract_links
from app.main import app
from app.repositories import user_repo, watch_repo

PW = "correct-horse-battery"
API = "/api/v1"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_AUTH", "1")
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(tmp_path / "d.db"))
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "test-secret")
    monkeypatch.setenv("FRAUDSHIELD_OUTBOX", str(tmp_path / "outbox"))
    monkeypatch.setenv("FRAUDSHIELD_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.delenv("FRAUDSHIELD_SMTP_HOST", raising=False)
    monkeypatch.delenv("EVOLUTION_API_URL", raising=False)
    from app.api.v1.endpoints import auth as auth_ep, webhooks
    auth_ep.limiter.reset(); auth_ep.register_limiter.reset(); webhooks.limiter.reset()
    user_repo.upsert("ana", auth.hash_password(PW), "analyst")
    return TestClient(app)


def register(c, name="sam", email="sam@example.com"):
    return c.post(f"{API}/auth/register", json={"username": name, "email": email, "password": PW})


def test_link_extractor():
    t = "Pay now https://evil.example/pay?x=1, or visit www.bad-site.com. Report.pdf is attached; also e.g. foo"
    assert extract_links(t) == ["https://evil.example/pay?x=1", "www.bad-site.com"]
    assert extract_links("no links here") == []
    assert extract_links("go to bit.ly/abc123!") == ["bit.ly/abc123"]


def test_phone_normalization():
    assert watch_repo.normalize_phone("050 123 4567") == "+971501234567"
    assert watch_repo.normalize_phone("00971501234567") == "+971501234567"
    assert watch_repo.normalize_phone("+44 7700 900123") == "+447700900123"
    with pytest.raises(ValueError):
        watch_repo.normalize_phone("12")


def test_register_creates_a_regular_user_and_signs_in(client):
    r = register(client)
    assert r.status_code == 201 and r.json()["role"] == "user"
    me = client.get(f"{API}/auth/me").json()
    assert me["username"] == "sam" and me["role"] == "user" and me["email"] == "sam@example.com"
    assert register(client).status_code == 409  # same username/email
    assert client.post(f"{API}/auth/register", json={"username": "x y", "email": "a@b.co", "password": PW}).status_code == 422


def test_register_cannot_pick_a_role(client):
    r = client.post(f"{API}/auth/register", json={"username": "evil", "email": "e@e.co", "password": PW, "role": "admin"})
    assert r.status_code == 201 and r.json()["role"] == "user"


def test_user_has_no_deep_search_or_staff_apis(client):
    register(client)
    assert client.post(f"{API}/scan", json={"url": "https://example.com", "deep": True}).status_code == 403
    assert client.get(f"{API}/queue").status_code == 403
    assert client.get(f"{API}/audit").status_code == 403
    assert client.post(f"{API}/scan", json={"url": "https://example.com"}).status_code == 200


def test_history_is_private_per_user(client):
    register(client, "sam", "sam@example.com")
    sid = client.post(f"{API}/scan", json={"url": "https://example.com/a"}).json()["scan_id"]
    assert [h["url"] for h in client.get(f"{API}/me/history").json()] == ["https://example.com/a"]
    other = TestClient(app)
    register(other, "kim", "kim@example.com")
    assert other.get(f"{API}/me/history").json() == []
    assert other.get(f"{API}/scans").json() == []
    assert other.get(f"{API}/scan/{sid}").status_code == 404
    client.post(f"{API}/auth/logout")
    staff = TestClient(app)
    staff.post(f"{API}/auth/login", json={"username": "ana", "password": PW})
    assert staff.get(f"{API}/scan/{sid}").status_code == 200


def test_me_requires_sign_in(client):
    assert client.get(f"{API}/me/summary").status_code == 401


def test_contacts_crud_and_limits(client):
    register(client)
    r = client.post(f"{API}/me/contacts", json={"kind": "phone", "value": "0501234567"})
    assert r.status_code == 201 and r.json()["value"] == "+971501234567"
    assert client.post(f"{API}/me/contacts", json={"kind": "phone", "value": "+971501234567"}).status_code == 422  # duplicate
    assert client.post(f"{API}/me/contacts", json={"kind": "email", "value": "nope"}).status_code == 422
    cid = client.post(f"{API}/me/contacts", json={"kind": "email", "value": "Me@Example.com"}).json()["id"]
    assert [c["value"] for c in client.get(f"{API}/me/contacts").json()] == ["+971501234567", "me@example.com"]
    assert client.delete(f"{API}/me/contacts/{cid}").status_code == 200
    assert client.delete(f"{API}/me/contacts/{cid}").status_code == 404


def test_settings_toggle_and_change_password(client):
    register(client)
    assert client.get(f"{API}/me/settings").json() == {"extension_enabled": True, "alerts_enabled": True}
    assert client.put(f"{API}/me/settings", json={"extension_enabled": False}).json()["extension_enabled"] is False
    assert client.post(f"{API}/auth/password", json={"current_password": "wrong-password", "new_password": "another-long-one"}).status_code == 403
    assert client.post(f"{API}/auth/password", json={"current_password": PW, "new_password": "another-long-one"}).status_code == 200
    assert client.post(f"{API}/auth/login", json={"username": "sam", "password": "another-long-one"}).status_code == 200


def _fake_scan(band, score):
    return lambda url, deep=False, **kw: {"scan_id": "s1", "url": url if "://" in url else "http://" + url, "score": score,
                                          "band": band, "reasons": [{"rule": "r", "points": 20, "reason": "looks like a bank"}]}


def _watch_number(c, number="+971501234567", email="sam@example.com"):
    register(c, email=email)
    c.post(f"{API}/me/contacts", json={"kind": "phone", "value": number})


def test_whatsapp_webhook_blocks_and_emails(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("likely_fraud", 92))
    _watch_number(client)
    payload = {"event": "messages.upsert", "sender": "971501234567@s.whatsapp.net",
               "data": {"key": {"remoteJid": "971555000111@s.whatsapp.net", "fromMe": False},
                        "message": {"conversation": "Your account is locked, verify at http://bank-login.example/verify"}}}
    r = client.post(f"{API}/webhooks/whatsapp", json=payload, headers={"x-webhook-secret": "hook-secret"})
    assert r.status_code == 200 and r.json()["handled"] == 1
    alerts = client.get(f"{API}/me/alerts").json()
    assert alerts[0]["action"] == "blocked" and alerts[0]["emailed"] is True and alerts[0]["channel"] == "whatsapp"
    mails = list((tmp_path / "outbox").glob("*.html"))
    assert mails and "bank-login.example" in mails[0].read_text()
    assert client.get(f"{API}/me/history?source=message").json()[0]["band"] == "likely_fraud"


def test_sms_webhook_safe_link_is_not_emailed_and_alerts_can_be_off(client, monkeypatch, tmp_path):
    _watch_number(client)
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("safe", 3))
    body = "From=%2B971555000111&To=%2B971501234567&Body=see+https%3A%2F%2Fexample.com"
    h = {"content-type": "application/x-www-form-urlencoded"}
    assert client.post(f"{API}/webhooks/sms?secret=hook-secret", content=body, headers=h).json()["handled"] == 1
    assert client.get(f"{API}/me/alerts").json()[0]["action"] == "allowed"
    assert not (tmp_path / "outbox").exists()
    client.put(f"{API}/me/settings", json={"alerts_enabled": False})
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("high_risk", 70))
    client.post(f"{API}/webhooks/sms?secret=hook-secret", content=body, headers=h)
    assert client.get(f"{API}/me/alerts").json()[0]["action"] == "blocked"
    assert not (tmp_path / "outbox").exists()  # alerts off: recorded but no email


def test_webhooks_reject_bad_secret_and_ignore_unwatched_numbers(client, monkeypatch):
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("likely_fraud", 92))
    _watch_number(client)
    assert client.post(f"{API}/webhooks/sms", content="To=x", headers={"content-type": "application/x-www-form-urlencoded"}).status_code == 401
    assert client.post(f"{API}/webhooks/whatsapp", json={}, headers={"x-webhook-secret": "nope"}).status_code == 401
    other = "From=%2B1&To=%2B971509999999&Body=http%3A%2F%2Fevil.example"
    r = client.post(f"{API}/webhooks/sms?secret=hook-secret", content=other, headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.json()["handled"] == 0 and client.get(f"{API}/me/alerts").json() == []
    monkeypatch.delenv("FRAUDSHIELD_WEBHOOK_SECRET")
    assert client.post(f"{API}/webhooks/sms?secret=", content="To=x", headers={"content-type": "application/x-www-form-urlencoded"}).status_code == 401


def test_outgoing_whatsapp_messages_are_ignored(client, monkeypatch):
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("likely_fraud", 92))
    _watch_number(client)
    payload = {"event": "messages.upsert", "sender": "971501234567@s.whatsapp.net",
               "data": {"key": {"remoteJid": "971555000111@s.whatsapp.net", "fromMe": True}, "message": {"conversation": "http://x.example"}}}
    assert client.post(f"{API}/webhooks/whatsapp", json=payload, headers={"x-webhook-secret": "hook-secret"}).json()["handled"] == 0


def test_extension_device_token_flow(client):
    register(client)
    tok = client.post(f"{API}/me/devices", json={"label": "Chrome"}).json()["token"]
    bearer = {"Authorization": f"Bearer {tok}"}
    anon = TestClient(app)
    assert anon.get(f"{API}/ext/config").status_code == 401
    assert anon.get(f"{API}/ext/config", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert anon.get(f"{API}/ext/config", headers=bearer).json() == {"enabled": True}
    visits = {"visits": [{"url": "https://example.com/x", "score": 10, "level": "low"},
                         {"url": "https://bad.example/login", "score": 85, "level": "high"}]}
    assert anon.post(f"{API}/ext/visits", json=visits, headers=bearer).json()["stored"] == 2
    hist = client.get(f"{API}/me/history?source=extension").json()
    assert {h["band"] for h in hist} == {"safe", "likely_fraud"}
    client.put(f"{API}/me/settings", json={"extension_enabled": False})
    assert anon.get(f"{API}/ext/config", headers=bearer).json() == {"enabled": False}
    assert anon.post(f"{API}/ext/visits", json=visits, headers=bearer).json()["stored"] == 0
    dev = client.get(f"{API}/me/devices").json()[0]
    assert "token" not in dev and client.delete(f"{API}/me/devices/{dev['id']}").status_code == 200
    assert anon.get(f"{API}/ext/config", headers=bearer).status_code == 401


# ---- WhatsApp linking from the website (gateway calls are faked) ----
def _fake_gateway(monkeypatch, state="connecting"):
    from app.alerts import whatsapp
    calls = {"created": [], "webhook": [], "deleted": []}
    monkeypatch.setenv("EVOLUTION_API_KEY", "k")
    monkeypatch.setattr(whatsapp, "create_instance", lambda i: calls["created"].append(i))
    monkeypatch.setattr(whatsapp, "set_webhook", lambda i: calls["webhook"].append(i))
    monkeypatch.setattr(whatsapp, "connect", lambda i, n=None: {"qr": "data:image/png;base64,AAA", "pairing_code": "ABCD-1234"})
    monkeypatch.setattr(whatsapp, "state", lambda i: state)
    monkeypatch.setattr(whatsapp, "delete_instance", lambda i: calls["deleted"].append(i))
    return calls


def test_whatsapp_link_flow(client, monkeypatch):
    calls = _fake_gateway(monkeypatch)
    register(client)
    r = client.post(f"{API}/me/whatsapp/connect", json={"number": "0568050565"})
    assert r.status_code == 200
    d = r.json()
    assert d["qr"].startswith("data:image") and d["pairing_code"] == "ABCD-1234" and d["number"] == "+971568050565" and not d["linked"]
    assert calls["created"] == calls["webhook"] and calls["created"][0].startswith("manee-") and "sam" not in calls["created"][0]
    assert client.get(f"{API}/me/contacts").json()[0]["value"] == "+971568050565"  # joined the watch list
    _fake_gateway(monkeypatch, state="open")
    s = client.get(f"{API}/me/whatsapp/status").json()
    assert s["linked"] is True and s["status"] == "open" and s["qr"] is None
    assert client.delete(f"{API}/me/whatsapp").json()["status"] == "none"
    assert client.get(f"{API}/me/whatsapp/status").json()["status"] == "none"


def test_whatsapp_link_needs_gateway_and_valid_number(client, monkeypatch):
    register(client)
    monkeypatch.delenv("EVOLUTION_API_KEY", raising=False)
    assert client.post(f"{API}/me/whatsapp/connect", json={"number": "0568050565"}).status_code == 503
    assert client.get(f"{API}/me/whatsapp/status").json()["available"] is False
    _fake_gateway(monkeypatch)
    assert client.post(f"{API}/me/whatsapp/connect", json={"number": "12"}).status_code == 422
    assert TestClient(app).post(f"{API}/me/whatsapp/connect", json={"number": "0568050565"}).status_code == 401


def test_webhook_uses_instance_to_find_the_user(client, monkeypatch):
    _fake_gateway(monkeypatch)
    monkeypatch.setattr("app.guard.guard_service.scan_url", _fake_scan("likely_fraud", 92))
    register(client)
    client.post(f"{API}/me/whatsapp/connect", json={"number": "0568050565"})
    from app.repositories import wa_link_repo
    inst = wa_link_repo.instance_name("sam")
    payload = {"event": "messages.upsert", "instance": inst,  # no top-level sender at all
               "data": {"key": {"remoteJid": "971555000111@s.whatsapp.net", "fromMe": False},
                        "message": {"conversation": "verify http://bank-login.example/v"}}}
    r = client.post(f"{API}/webhooks/whatsapp", json=payload, headers={"x-webhook-secret": "hook-secret"})
    assert r.json()["handled"] == 1
    assert client.get(f"{API}/me/alerts").json()[0]["action"] == "blocked"
    payload["instance"] = "manee-unknown"
    assert client.post(f"{API}/webhooks/whatsapp", json=payload, headers={"x-webhook-secret": "hook-secret"}).json()["handled"] == 0
