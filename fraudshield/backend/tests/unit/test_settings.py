import pytest
from fastapi.testclient import TestClient

from app.engine.pipeline import run_pipeline
from app.engine.scoring import tuning
from app.main import app

BAD = "http://adcb-secure-login.example.com/verify"  # reserved example domain; nothing real is contacted


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(tmp_path / "d.db"))
    tuning._invalidate()
    yield TestClient(app)
    tuning._invalidate()


def put_rule(c, name, points, reason="tuning after review"):
    return c.put(f"/api/v1/admin/settings/rules/{name}", json={"points": points, "reason": reason})


def test_defaults_come_from_the_yaml(client):
    s = client.get("/api/v1/admin/settings").json()
    rules = {r["name"]: r for r in s["rules"]}
    assert rules["brand_name_not_official_domain"]["current"] == rules["brand_name_not_official_domain"]["default"] == 35
    assert s["cutoffs"]["current"] == [30, 60, 80]
    assert [b["name"] for b in s["bands"]] == ["safe", "suspicious", "high_risk", "likely_fraud"]
    assert s["bands"][0]["max"] == 29 and s["bands"][-1]["max"] == 100


def test_a_weight_change_takes_effect_immediately_without_restart(client):
    before = run_pipeline(BAD)["score"]
    assert put_rule(client, "brand_name_not_official_domain", 5).status_code == 200
    after = run_pipeline(BAD)["score"]
    assert after == before - 30
    assert client.post("/api/v1/scan", json={"url": BAD}).json()["score"] == after  # the live API uses it too
    # setting it back to the default removes the override
    put_rule(client, "brand_name_not_official_domain", 35)
    assert run_pipeline(BAD)["score"] == before
    rules = {r["name"]: r for r in client.get("/api/v1/admin/settings").json()["rules"]}
    assert rules["brand_name_not_official_domain"]["changed"] is False


def test_zero_switches_a_rule_off(client):
    put_rule(client, "brand_name_not_official_domain", 0)
    assert "brand_name_not_official_domain" not in {r["rule"] for r in run_pipeline(BAD)["reasons"]}


def test_cutoffs_move_the_bands(client):
    score = run_pipeline(BAD)["score"]
    band = run_pipeline(BAD)["band"]
    r = client.put("/api/v1/admin/settings/cutoffs", json={"suspicious": 10, "high_risk": 20, "likely_fraud": score, "reason": "stricter"})
    assert r.status_code == 200
    assert run_pipeline(BAD)["band"] == "likely_fraud" != band


def test_invalid_changes_are_rejected(client):
    assert put_rule(client, "no_such_rule", 5).status_code == 404
    assert put_rule(client, "ip_host", 999).status_code == 422
    assert put_rule(client, "ip_host", -1).status_code == 422
    assert put_rule(client, "ip_host", 5, reason="").status_code == 422  # a reason is required
    bad = {"suspicious": 60, "high_risk": 40, "likely_fraud": 80, "reason": "oops"}
    assert client.put("/api/v1/admin/settings/cutoffs", json=bad).status_code == 422
    assert client.put("/api/v1/admin/settings/cutoffs", json={**bad, "suspicious": 0, "high_risk": 50}).status_code == 422


def test_history_audit_and_reset(client):
    put_rule(client, "ip_host", 5, "too noisy on test data")
    client.put("/api/v1/admin/settings/cutoffs", json={"suspicious": 35, "high_risk": 60, "likely_fraud": 80, "reason": "calmer"})
    s = client.get("/api/v1/admin/settings").json()
    assert [h["key"] for h in s["history"]][:2] == ["cutoffs", "rule.ip_host"]
    assert s["history"][1]["old_value"] is None and s["history"][1]["new_value"] == "5"
    assert s["history"][1]["reason"] == "too noisy on test data"
    audit = [a["action"] for a in client.get("/api/v1/audit").json()]
    assert "settings.rule" in audit and "settings.cutoffs" in audit
    r = client.post("/api/v1/admin/settings/reset", json={"reason": "back to defaults"}).json()
    assert r["cutoffs"]["current"] == [30, 60, 80] and not any(x["changed"] for x in r["rules"])
    assert len(client.get("/api/v1/admin/settings").json()["history"]) >= 4  # history is never erased


def test_preview_shows_the_effect_without_saving(client):
    for _ in range(2):
        client.post("/api/v1/scan", json={"url": BAD})
    p = client.post("/api/v1/admin/settings/preview", json={"rules": {"brand_name_not_official_domain": 0}}).json()
    assert p["scans_checked"] == 2 and p["changed_count"] == 2
    assert p["changed"][0]["new_score"] < p["changed"][0]["old_score"]
    assert client.get("/api/v1/admin/settings").json()["rules"][0]["current"] == 35  # nothing saved
    assert client.post("/api/v1/admin/settings/preview", json={"rules": {"nope": 1}}).status_code == 404
    same = client.post("/api/v1/admin/settings/preview", json={}).json()
    assert same["changed_count"] == 0  # re-scoring with the current numbers reproduces the stored scores


def test_admin_only(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_AUTH", "1")
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_SECRET", "s")
    from app.core import auth
    from app.repositories import user_repo
    user_repo.upsert("ana", auth.hash_password("correct-horse-1"), "analyst")
    c = TestClient(app)
    assert c.get("/api/v1/admin/settings").status_code == 401
    c.post("/api/v1/auth/login", json={"username": "ana", "password": "correct-horse-1"})
    assert c.get("/api/v1/admin/settings").status_code == 403
    assert c.put("/api/v1/admin/settings/rules/ip_host", json={"points": 1, "reason": "sneaky"}).status_code == 403
