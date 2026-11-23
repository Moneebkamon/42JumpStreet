import json
from pathlib import Path

import pytest

from app.engine.pipeline import run_pipeline
from app.engine.scoring.rules import evaluate_rules
from app.ml import model_loader
from app.ml.predictor import ml_features, phish_probability
from app.analyzers.url_analyzer.normalizer import normalize

REFERENCE = Path(__file__).parent.parent / "fixtures" / "urlbert_reference.json"
needs_model = pytest.mark.skipif(
    not (model_loader.DEFAULT_DIR / "model.safetensors").exists(), reason="model files not downloaded (see ml/README.md)"
)


@pytest.fixture
def model_on(monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_ML", "1")


def test_model_is_off_by_default_in_tests_and_reports_unavailable():
    assert phish_probability("example.org/") is None
    assert ml_features(normalize("https://example.org/")) == {"ml_available": 0}


def test_missing_model_files_are_not_an_error(monkeypatch, tmp_path):
    monkeypatch.setenv("FRAUDSHIELD_ML", "1")
    monkeypatch.setenv("FRAUDSHIELD_MODEL_DIR", str(tmp_path))
    assert phish_probability("example.org/") is None


@needs_model
def test_numpy_model_matches_the_torch_reference(model_on):
    """Reference probabilities were produced by ml/tiny_bert.py (torch) on the same weights."""
    ref = json.loads(REFERENCE.read_text())
    assert len(ref) >= 10
    for row in ref:
        assert phish_probability(row["text"]) == pytest.approx(row["torch_prob"], abs=1e-3), row["text"]


@needs_model
def test_model_input_drops_the_scheme(model_on):
    f = ml_features(normalize("https://adcb-secure-login.top/verify"))
    assert f["ml_available"] == 1 and f["ml_phish_prob"] == pytest.approx(0.9996, abs=1e-3)


@needs_model
def test_pipeline_adds_a_reason_but_the_model_alone_cannot_make_it_suspicious(model_on):
    r = run_pipeline("http://paypal-account-verify.xyz/login.php?id=123", use_network=False)
    assert r["features"]["ml_available"] == 1
    assert any(h["rule"].startswith("ml_url_pattern") for h in r["reasons"])
    # a non-brand link the model dislikes gets at most +15 from it
    plain = run_pipeline("http://192.168.0.1/admin", use_network=False)
    ml_points = sum(h["points"] for h in plain["reasons"] if h["rule"].startswith("ml_url_pattern"))
    assert 0 < ml_points <= 15


def test_rule_tiers():
    strong = {h["rule"] for h in evaluate_rules({"ml_phish_prob": 0.97})}
    mid = {h["rule"] for h in evaluate_rules({"ml_phish_prob": 0.9})}
    low = {h["rule"] for h in evaluate_rules({"ml_phish_prob": 0.5})}
    none = {h["rule"] for h in evaluate_rules({"ml_available": 0})}
    assert strong == {"ml_url_pattern_strong"} and mid == {"ml_url_pattern"} and not low and not none
