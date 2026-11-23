"""Run the analyzers, then the rules, then overrides and bands. Returns one result dict."""
from app.engine.explainer import explain
from app.engine.feature_assembler import assemble_features
from app.engine.scoring.bands import band_for
from app.engine.scoring.combiner import combine
from app.engine.scoring.overrides import apply_overrides
from app.engine.scoring.rules import evaluate_rules


def run_pipeline(raw_url: str, use_network: bool = False, deep: bool = False) -> dict:
    """Raises ValueError if the URL is unusable."""
    assembled = assemble_features(raw_url, use_network=use_network, deep=deep)
    features = assembled["features"]

    hits = evaluate_rules(features)
    score = combine(sum(h["points"] for h in hits))
    score, notes = apply_overrides(score, features)
    band = band_for(score)

    ok, failed = assembled["analyzers_ok"], assembled["analyzers_failed"]
    reasons = [{"rule": "override", "points": 0, "reason": n} for n in notes] + hits
    result = {
        "url": assembled["url"],
        "score": score,
        "band": band["name"],
        "action": band["action"],
        "confidence": round(len(ok) / (len(ok) + len(failed)), 2),
        "reasons": reasons,
        "analyzers_ok": ok,
        "analyzers_failed": failed,
        "features": features,
        "page": assembled["page"],
    }
    result["explanation"] = explain(result)
    return result
