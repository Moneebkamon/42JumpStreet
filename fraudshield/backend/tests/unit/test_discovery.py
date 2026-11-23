import json

import pytest
from fastapi.testclient import TestClient

from app.alerts import dispatcher
from app.discovery import domain_watch
from app.discovery.ct_stream_listener import DEFAULT_SAMPLE, rate_capped, replay_source, with_reconnect
from app.discovery.ingest import ingest
from app.discovery.prefilter import clean_domain, prefilter
from app.main import app
from app.services.scan_service import scan_url


def ev(seq, *domains, issued="2026-11-20T08:00:00Z"):
    return {"seq": seq, "issued_at": issued, "domains": list(domains)}


# ---- prefilter ----
def test_clean_domain_strips_wildcard_and_dot():
    assert clean_domain("*.Example.COM.") == "example.com"


@pytest.mark.parametrize("domain,reason", [
    ("adcb-secure-login.top", "brand:adcb"),
    ("adcb.com.verify-now.top", "brand:adcb"),
    ("sa1ik-recharge.com", "brand:salik"),
    ("xn--80ak6aa92e.com", "homoglyph"),
    ("blue-login.xyz", "keyword_risky_tld"),
    ("secure-account-update.com", "keyword_hyphens"),
])
def test_prefilter_keeps_suspicious(domain, reason):
    r = prefilter(domain)
    assert r.keep and reason in r.reasons, r


@pytest.mark.parametrize("domain", [
    "bluepeak-studio.com", "mapleriver.ae", "www.adcb.com", "online.adcb.com", "tamm.abudhabi", "10.0.0.1",
    "login.com",  # keyword alone on a normal TLD is not enough
])
def test_prefilter_drops_ordinary_and_official(domain):
    assert not prefilter(domain).keep, domain


def test_sample_prefilter_recall_and_pass_through():
    """Measured on the simulated sample: planted scams are kept, benign and official domains mostly dropped."""
    kept = {"lookalike": 0, "homoglyph": 0, "keyword": 0}
    planted = dict.fromkeys(kept, 0)
    benign = benign_kept = domains = passed = 0
    official_kept = 0
    for e in replay_source(DEFAULT_SAMPLE):
        d = e["domains"][0]
        r = prefilter(d)
        domains += 1
        passed += r.keep
        if e["label"] in planted:
            planted[e["label"]] += 1
            kept[e["label"]] += r.keep
        elif e["label"] == "benign":
            benign += 1
            benign_kept += r.keep
        else:
            official_kept += r.keep
    assert official_kept == 0
    assert kept["lookalike"] / planted["lookalike"] >= 0.9
    assert benign_kept / benign <= 0.05
    assert passed / domains <= 0.25


# ---- listener ----
def test_replay_source_reads_jsonl(tmp_path):
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps(ev(1, "a.com")) + "\n\n" + json.dumps(ev(2, "b.com")) + "\n", encoding="utf-8")
    assert [e["seq"] for e in replay_source(f)] == [1, 2]


def test_with_reconnect_restarts_after_failure():
    calls, waits = [], []

    def factory():
        calls.append(1)
        if len(calls) == 1:
            yield ev(1, "a.com")
            raise ConnectionError("dropped")
        yield ev(2, "b.com")

    out = list(with_reconnect(factory, max_retries=3, backoff_seconds=1, sleep=waits.append))
    assert [e["seq"] for e in out] == [1, 2] and waits == [1]


def test_with_reconnect_gives_up():
    def factory():
        raise ConnectionError("down")
        yield  # pragma: no cover

    waits = []
    with pytest.raises(ConnectionError):
        list(with_reconnect(factory, max_retries=2, backoff_seconds=1, sleep=waits.append))
    assert waits == [1, 2]


def test_rate_capped_spaces_events():
    now, slept = [0.0], []

    def sleep(s):
        slept.append(s)
        now[0] += s

    out = list(rate_capped([ev(i, "a.com") for i in range(3)], 2, clock=lambda: now[0], sleep=sleep))
    assert len(out) == 3 and sum(slept) == pytest.approx(1.0)


# ---- ingest + store ----
def test_ingest_scores_stores_and_measures(tmp_path):
    db = tmp_path / "d.db"
    events = [ev(1, "adcb-secure-login.top", "www.adcb-secure-login.top"), ev(2, "bluepeak-studio.com"), ev(3, "www.adcb.com")]
    summary = ingest(events, simulated=True, notify=lambda d: False, db_file=db)
    assert summary["domains_seen"] == 3  # www. variant collapsed into the bare domain
    assert summary["kept"] == 1 and summary["scored"] == 1
    assert summary["pass_through_rate"] == pytest.approx(1 / 3, abs=1e-3)

    rows = domain_watch.list_detections(path=db)
    assert len(rows) == 1
    r = rows[0]
    assert r["domain"] == "adcb-secure-login.top" and r["brand_id"] == "adcb" and r["simulated"]
    assert r["score"] > 0 and r["reasons"] and r["issue_to_detection_s"] >= 0

    again = ingest(events, simulated=True, notify=lambda d: False, db_file=db)
    assert again["scored"] == 0  # already known: not scored twice
    assert domain_watch.stats(db)["detections"] == 1


def test_feed_filters(tmp_path):
    db = tmp_path / "d.db"
    ingest([ev(1, "adcb-secure-login.top", "sa1ik-recharge.com")], simulated=True, notify=lambda d: False, db_file=db)
    assert len(domain_watch.list_detections(path=db)) == 2
    assert [r["brand_id"] for r in domain_watch.list_detections(brand="salik", path=db)] == ["salik"]
    assert domain_watch.list_detections(min_score=101, path=db) == []
    assert domain_watch.list_detections(source="nope", path=db) == []


def test_stats_empty_database(tmp_path):
    s = domain_watch.stats(tmp_path / "empty.db")
    assert s["detections"] == 0 and s["pass_through_rate"] == 0.0 and s["simulated"] is False


# ---- alerts ----
def _det(band="high_risk"):
    return {"domain": "x.top", "score": 70, "band": band, "brand_name": "ADCB", "simulated": True,
            "reasons": [{"reason": "uses the brand name"}]}


def test_alert_needs_configuration(monkeypatch):
    sent = []
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert dispatcher.notify(_det(), sender=lambda *a: sent.append(a) or True) is False and not sent


def test_alert_sent_for_high_risk_only(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "c")
    sent = []
    send = lambda text, token, chat: sent.append((text, token, chat)) or True  # noqa: E731
    assert dispatcher.notify(_det("suspicious"), sender=send) is False
    assert dispatcher.notify(_det("high_risk"), sender=send) is True
    assert "[SIMULATED]" in sent[0][0] and "x.top" in sent[0][0]


def test_alerts_are_capped_per_run(tmp_path):
    n = []
    ingest([ev(i, f"adcb-secure-login{i}.top") for i in range(12)], simulated=True,
           notify=lambda d: n.append(1) or True, db_file=tmp_path / "d.db")
    assert len(n) <= 5


# ---- API and cache pre-warm ----
def test_api_feed_and_stats(tmp_path, monkeypatch):
    db = tmp_path / "api.db"
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(db))
    ingest([ev(1, "adcb-secure-login.top")], simulated=True, notify=lambda d: False, db_file=db)
    c = TestClient(app)
    feed = c.get("/api/v1/feed?min_score=1&brand=adcb").json()
    assert len(feed) == 1 and feed[0]["domain"] == "adcb-secure-login.top"
    assert c.get("/api/v1/feed?limit=0").status_code == 422
    stats = c.get("/api/v1/stats").json()
    assert stats["detections"] == 1 and stats["simulated"] is True


def test_flagged_domain_is_answered_from_cache(tmp_path, monkeypatch):
    db = tmp_path / "cache.db"
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(db))
    ingest([ev(1, "adcb-secure-login.top")], simulated=True, notify=lambda d: False, db_file=db)

    hit = scan_url("https://adcb-secure-login.top")
    assert hit["cached"] is True and hit["score"] > 0
    assert scan_url("https://adcb-secure-login.top/other/page").get("cached") is None  # path -> fresh scan
    assert scan_url("https://unseen-domain.example").get("cached") is None


def test_scan_without_database_does_not_create_one(tmp_path, monkeypatch):
    db = tmp_path / "never.db"
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(db))
    scan_url("https://adcb-secure-login.top")
    assert not db.exists()
