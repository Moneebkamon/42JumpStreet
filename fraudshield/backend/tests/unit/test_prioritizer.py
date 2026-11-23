import pytest
from fastapi.testclient import TestClient

from app.discovery.ingest import ingest
from app.engine.prioritizer import prioritize, value
from app.main import app


def d(domain, score, brand=""):
    return {"domain": domain, "score": score, "brand_id": brand}


def test_value_peaks_for_serious_but_uncertain_scores():
    assert value(d("a", 0)) == 0
    # a 70 beats a 20 (more suspicious) and beats a 100 only if the 100 is no more informative...
    assert value(d("a", 70)) > value(d("a", 20))
    # same suspicion band, bank brand is weighted higher than an unknown one
    assert value(d("a", 60, "adcb")) > value(d("a", 60))


def test_budget_is_respected_and_best_first():
    pool = [d(f"x{i}.top", s) for i, s in enumerate([10, 70, 55, 90, 40])]
    picked = prioritize(pool, budget_seconds=10, cost_seconds=5)  # room for 2
    assert len(picked) == 2
    assert picked[0]["priority"] >= picked[1]["priority"]
    assert sum(p["est_cost_s"] for p in picked) <= 10
    chosen = {p["domain"] for p in picked}
    assert chosen == set(sorted(pool, key=lambda x: -value(x))[0:2][i]["domain"] for i in range(2))


def test_zero_scores_and_bad_budget_are_skipped():
    assert prioritize([d("a", 0)], 100) == []
    assert prioritize([d("a", 50)], 0) == []
    assert prioritize([d("a", 50)], 4, cost_seconds=5) == []  # cannot afford even one


def test_deterministic_ties():
    pool = [d("b.top", 50), d("a.top", 50)]
    assert [p["domain"] for p in prioritize(pool, 5)] == ["a.top"]


def test_triage_endpoint_recommends_only(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    monkeypatch.setenv("FRAUDSHIELD_DISCOVERY_DB", str(db))
    ingest([{"seq": 1, "issued_at": "2026-11-20T08:00:00Z",
             "domains": ["adcb-secure-login.top", "sa1ik-recharge.com", "dhl-parcel-verify.xyz"]}],
           simulated=True, notify=lambda x: False, db_file=db)
    c = TestClient(app)
    got = c.get("/api/v1/triage?budget_seconds=10").json()
    assert len(got) == 2 and got[0]["priority"] >= got[1]["priority"]
    assert c.get("/api/v1/triage?budget_seconds=0").status_code == 422
