import pytest
from fastapi.testclient import TestClient

from app.engine.explainer import explain
from app.engine.explainer.evidence_selector import select
from app.engine.pipeline import run_pipeline
from app.main import app


def result(band="high_risk", action="warn", reasons=(), failed=(), page=None):
    return {"band": band, "action": action, "reasons": list(reasons), "analyzers_failed": list(failed), "page": page}


def r(rule, points, text="x"):
    return {"rule": rule, "points": points, "reason": text}


def test_selects_highest_points_and_overrides_first():
    res = result(reasons=[r("risky_tld", 15), r("override", 0, "Domain is listed in a known threat feed"),
                          r("brand_name_not_official_domain", 35), r("url_shortener", 10), r("ip_host", 15),
                          r("hidden_content", 10)])
    picked = [f["rule"] for f in select(res)]
    assert picked[0] == "override" and picked[1] == "brand_name_not_official_domain" and len(picked) == 4
    assert "url_shortener" not in picked or "hidden_content" not in picked  # the lowest are dropped


def test_only_fired_rules_appear_in_the_text():
    text = explain(result(reasons=[r("ip_host", 15), r("risky_tld", 15)]))
    assert "raw IP address" in text and "domain ending" in text
    assert "password" not in text.split("Mainly because")[1].split(".")[0]  # no clause about forms invented


def test_override_wording_and_official_domain():
    off = explain(result("safe", "allow", [r("override", 0, "Domain is an official domain of ADCB")]))
    assert "official domain of ADCB" in off and "minor warning signs" not in off
    bad = explain(result("likely_fraud", "review", [r("override", 0, "Domain is listed in a known threat feed")]))
    assert "known threat feed" in bad and "very likely to be a scam" in bad and "Report it" in bad


def test_caveats_are_honest():
    t = explain(result("high_risk", "warn", [r("ip_host", 15)], failed=["domain_lookup"]))
    assert "some checks could not run" in t and "only the link was checked" in t
    deep = explain(result("high_risk", "warn", [r("ip_host", 15)], page={"title": "x"}))
    assert "only the link was checked" not in deep


def test_model_only_signal_is_flagged_as_weak():
    t = explain(result("suspicious", "monitor", [r("ml_url_pattern", 8)]))
    assert "only signal" in t and "often wrong" in t


def test_clean_link_has_no_scare_wording():
    t = explain(result("safe", "allow", []))
    assert "no strong warning signs" in t and "Mainly because" not in t


def test_pipeline_result_carries_an_explanation():
    out = run_pipeline("https://adcb-secure-login.example.com/verify")
    from app.engine.explainer.fallback_templates import OPENING
    assert out["explanation"].startswith(OPENING[out["band"]])  # the wording follows the real verdict
    assert out["explanation"].count(".") >= 3


def test_api_returns_it_and_fills_it_for_old_stored_scans(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB", str(tmp_path / "f.db"))
    c = TestClient(app)
    posted = c.post("/api/v1/scan", json={"url": "http://bit.ly/abc"}).json()
    assert posted["explanation"]
    # simulate a scan stored before explanations existed
    import json, sqlite3
    con = sqlite3.connect(tmp_path / "f.db")
    row = con.execute("SELECT id, result_json FROM scans").fetchone()
    data = json.loads(row[1]); data.pop("explanation");
    con.execute("UPDATE scans SET result_json = ? WHERE id = ?", (json.dumps(data), row[0])); con.commit(); con.close()
    assert c.get(f"/api/v1/scan/{row[0]}").json()["explanation"]
