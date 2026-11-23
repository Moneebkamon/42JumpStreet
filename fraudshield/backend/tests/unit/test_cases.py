import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.discovery.ingest import ingest
from app.main import app
from app.services import citizen_report_service, priority_service

BAD = "http://adcb-secure-login.example.com/verify"  # reserved example domain: nothing real is ever contacted


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(tmp_path / "d.db"))
    citizen_report_service.limiter.reset()
    return TestClient(app)


def scan(c, url=BAD):
    return c.post("/api/v1/scan", json={"url": url}).json()["scan_id"]


def open_case(c, url=BAD):
    r = c.post("/api/v1/cases", json={"source": "scan", "source_ref": scan(c, url)})
    assert r.status_code == 201, r.text
    return r.json()["ref"]


def move(c, ref, to, reason="checked by analyst"):
    return c.patch(f"/api/v1/cases/{ref}", json={"to_status": to, "reason": reason})


# ---- cases and workflow ----
def test_case_is_opened_from_a_scan(client):
    ref = open_case(client)
    case = client.get(f"/api/v1/cases/{ref}").json()
    assert ref == "FS-0001" and case["status"] == "new" and case["score"] > 0
    assert case["allowed_next"] == ["under_review"]
    assert case["events"][0]["kind"] == "created"
    assert client.get("/api/v1/cases").json()[0]["ref"] == ref


def test_unknown_source_and_missing_case(client):
    assert client.post("/api/v1/cases", json={"source": "scan", "source_ref": "nope"}).status_code == 404
    assert client.post("/api/v1/cases", json={"source": "magic", "source_ref": "x"}).status_code == 422
    assert client.get("/api/v1/cases/FS-9999").status_code == 404


def test_duplicate_open_case_for_the_same_domain_is_refused(client):
    ref = open_case(client)
    r = client.post("/api/v1/cases", json={"source": "scan", "source_ref": scan(client)})
    assert r.status_code == 409 and r.json()["ref"] == ref


def test_full_happy_path_and_invalid_transitions(client):
    ref = open_case(client)
    assert move(client, ref, "confirmed").status_code == 409  # cannot skip "under review"
    assert move(client, ref, "under_review", "").status_code == 422  # a reason is required
    assert move(client, ref, "under_review").status_code == 200
    assert move(client, ref, "confirmed").status_code == 200
    assert move(client, ref, "takedown_requested", "sent by analyst").status_code == 200
    assert move(client, ref, "taken_down", "host confirmed removal").status_code == 200
    assert move(client, ref, "closed").status_code == 200
    final = client.get(f"/api/v1/cases/{ref}").json()
    assert final["status"] == "closed" and final["allowed_next"] == []
    assert move(client, ref, "under_review").status_code == 409  # closed is final
    status_events = [e for e in final["events"] if e["kind"] == "status"]
    assert [e["to_status"] for e in status_events] == ["under_review", "confirmed", "takedown_requested", "taken_down", "closed"]
    assert all(e["text"] and e["actor"] for e in status_events)


def test_false_positive_from_a_review_state_only(client):
    a = open_case(client)
    assert move(client, a, "false_positive").status_code == 409  # not from "new"
    move(client, a, "under_review")
    assert move(client, a, "false_positive", "legitimate site").status_code == 200
    # a finished case frees the domain for a new one
    assert client.post("/api/v1/cases", json={"source": "scan", "source_ref": scan(client)}).status_code == 201


def test_notes(client):
    ref = open_case(client)
    r = client.post(f"/api/v1/cases/{ref}/notes", json={"text": "called the brand"})
    assert r.status_code == 201 and r.json()["events"][-1]["text"] == "called the brand"
    assert client.post(f"/api/v1/cases/{ref}/notes", json={"text": "   "}).status_code == 422


# ---- evidence ----
def test_evidence_is_hashed_and_verifiable(client):
    ref = open_case(client)
    items = client.post(f"/api/v1/cases/{ref}/evidence").json()
    assert {i["kind"] for i in items} >= {"scan_result", "reasons", "features"}
    assert all(len(i["sha256"]) == 64 and i["captured_at"].endswith("Z") and i["tool_version"] for i in items)
    for i in items:
        v = client.get(f"/api/v1/evidence/{i['id']}/verify").json()
        assert v["ok"] is True and v["stored_sha256"] == v["recomputed_sha256"]
    assert client.get("/api/v1/evidence/999/verify").status_code == 404


def test_tampered_evidence_is_detected(client, tmp_path):
    ref = open_case(client)
    first = client.post(f"/api/v1/cases/{ref}/evidence").json()[0]["id"]
    con = sqlite3.connect(tmp_path / "f.db")
    con.execute("UPDATE evidence SET content = content || ' ' WHERE id = ?", (first,))
    con.commit()
    con.close()
    v = client.get(f"/api/v1/evidence/{first}/verify").json()
    assert v["ok"] is False and v["stored_sha256"] != v["recomputed_sha256"]


# ---- takedown drafts ----
def test_drafts_need_review_and_never_claim_more_than_the_status(client):
    ref = open_case(client)
    assert client.post(f"/api/v1/cases/{ref}/takedown-drafts", json={"recipient_type": "brand"}).status_code == 409
    move(client, ref, "under_review")
    assert client.post(f"/api/v1/cases/{ref}/takedown-drafts", json={"recipient_type": "nobody"}).status_code == 422

    d = client.post(f"/api/v1/cases/{ref}/takedown-drafts", json={"recipient_type": "registrar_hosting"}).json()
    assert "NOT YET CONFIRMED" in d["body"] and "suspected" in d["subject"].lower()
    assert "has not been sent" in d["body"] and "No evidence has been frozen" in d["body"]

    client.post(f"/api/v1/cases/{ref}/evidence")
    move(client, ref, "confirmed")
    d2 = client.post(f"/api/v1/cases/{ref}/takedown-drafts", json={"recipient_type": "search_safety"}).json()
    assert "confirmed by an analyst" in d2["body"] and "NOT YET CONFIRMED" not in d2["body"]
    assert "scan_result:" in d2["body"]  # evidence hashes are listed

    exp = client.get(f"/api/v1/takedowns/{d2['id']}/export")
    assert exp.status_code == 200 and "attachment" in exp.headers["content-disposition"]
    assert exp.text.startswith("Subject:") and ref in exp.headers["content-disposition"]
    assert client.get(f"/api/v1/takedowns/{d2['id']}").json()["exported_at"]


# ---- audit ----
def test_every_sensitive_action_is_in_the_audit_log(client):
    ref = open_case(client)
    move(client, ref, "under_review")
    items = client.post(f"/api/v1/cases/{ref}/evidence").json()
    client.get(f"/api/v1/evidence/{items[0]['id']}")
    client.get(f"/api/v1/evidence/{items[0]['id']}/verify")
    d = client.post(f"/api/v1/cases/{ref}/takedown-drafts", json={"recipient_type": "brand"}).json()
    client.get(f"/api/v1/takedowns/{d['id']}/export", headers={"X-Actor": "dana"})
    actions = [(a["action"], a["actor"]) for a in client.get("/api/v1/audit").json()]
    for expected in ("case.create", "case.status", "evidence.freeze", "evidence.view", "evidence.verify",
                     "takedown.draft", "takedown.export"):
        assert expected in [a for a, _ in actions], expected
    assert ("takedown.export", "dana") in actions


# ---- citizen reports ----
def report(c, url=BAD, **kw):
    return c.post("/api/v1/citizen-reports", json={"url": url, **kw})


def test_citizen_report_is_scored_and_stored(client):
    r = report(client, note="got this by SMS")
    assert r.status_code == 201
    body = r.json()
    assert body["ref"] == "CR-0001" and body["score"] > 0 and body["advice"]
    assert client.get("/api/v1/citizen-reports").json()[0]["note"] == "got this by SMS"


def test_report_abuse_protection(client):
    assert report(client, website="http://spam.example").status_code == 422  # honeypot filled
    assert report(client, url="http://").status_code == 422
    assert client.post("/api/v1/citizen-reports", json={"url": "x" * 3000}).status_code == 422
    assert report(client, note="n" * 1001).status_code == 422
    for _ in range(5):
        assert report(client).status_code == 201
    assert report(client).status_code == 429  # sixth in the window


def test_reports_raise_priority_and_feed_the_queue(client):
    base = priority_service.compute(50, "adcb", "x.example.com", reports=0, scans=0)["priority"]
    more = priority_service.compute(50, "adcb", "x.example.com", reports=3, scans=0)["priority"]
    assert more > base
    assert priority_service.compute(50, "nobrand", "x.example.com", reports=0, scans=0)["priority"] < base

    report(client)
    queue = client.get("/api/v1/queue").json()
    assert queue and queue[0]["kind"] == "report" and queue[0]["ref"] == "CR-0001"
    client.post("/api/v1/cases", json={"source": "report", "source_ref": "CR-0001"})
    assert client.get("/api/v1/queue").json() == []  # now it has a case


def test_detections_feed_the_queue_and_can_become_cases(client, tmp_path):
    ingest([{"seq": 1, "issued_at": "2026-11-20T08:00:00Z", "domains": ["adcb-secure-login.top"]}],
           simulated=True, notify=lambda d: False, db_file=tmp_path / "d.db")
    q = client.get("/api/v1/queue").json()
    assert [i["ref"] for i in q] == ["adcb-secure-login.top"] and q[0]["kind"] == "detection"
    r = client.post("/api/v1/cases", json={"source": "detection", "source_ref": "adcb-secure-login.top"})
    assert r.status_code == 201 and r.json()["brand_id"] == "adcb"
    assert client.get("/api/v1/queue").json() == []
