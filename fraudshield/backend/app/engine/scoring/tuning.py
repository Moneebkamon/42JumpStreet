"""The scoring numbers an admin may change without redeploying: rule points and the three band cutoffs.

Defaults come from config/rule_weights.yaml and config/risk_bands.yaml. Admin changes are stored in the database and win
over the defaults. Every change needs a reason and is recorded in an append-only history. The effective values are cached
per database and refreshed on every change (this process only; a multi-server setup would need a shared cache).
"""
import json

from app.core.errors import NotFound

from app.core.config import load_config
from app.repositories import scan_repo, settings_repo
from app.repositories.scan_repo import db_path

MAX_POINTS = 60  # one rule alone may never decide everything
_cache: dict[str, dict] = {}


def _invalidate() -> None:
    _cache.clear()


def _state() -> dict:
    key = str(db_path())
    if key not in _cache:
        overrides = settings_repo.all_values()
        defaults = {k: int(v) for k, v in load_config("rule_weights").get("rules", {}).items()}
        weights = dict(defaults)
        for name in defaults:
            if f"rule.{name}" in overrides:
                weights[name] = int(overrides[f"rule.{name}"])
        bands = load_config("risk_bands")["bands"]
        default_cutoffs = [b["min"] for b in bands[1:]]
        cutoffs = json.loads(overrides["cutoffs"]) if "cutoffs" in overrides else default_cutoffs
        _cache[key] = {"defaults": defaults, "weights": weights, "default_cutoffs": default_cutoffs, "cutoffs": cutoffs}
    return _cache[key]


def rule_weights() -> dict[str, int]:
    return dict(_state()["weights"])


def default_rule_weights() -> dict[str, int]:
    return dict(_state()["defaults"])


def cutoffs() -> list[int]:
    return list(_state()["cutoffs"])


def default_cutoffs() -> list[int]:
    return list(_state()["default_cutoffs"])


def bands(cut: list[int] | None = None) -> list[dict]:
    """The bands with min/max filled in from three cutoffs: [suspicious_min, high_risk_min, likely_fraud_min]."""
    base = load_config("risk_bands")["bands"]
    cut = cut or cutoffs()
    mins = [0, *cut]
    return [
        {"name": b["name"], "action": b["action"], "min": mins[i], "max": (mins[i + 1] - 1) if i + 1 < len(mins) else 100}
        for i, b in enumerate(base)
    ]


def validate_cutoffs(cut: list[int]) -> list[int]:
    if len(cut) != 3 or any(not isinstance(c, int) for c in cut):
        raise ValueError("three whole-number cutoffs are needed: suspicious, high risk, likely fraud")
    if not (1 <= cut[0] < cut[1] < cut[2] <= 100):
        raise ValueError("cutoffs must rise: 1 <= suspicious < high risk < likely fraud <= 100")
    return cut


def set_rule(name: str, points: int, actor: str, reason: str) -> None:
    if name not in default_rule_weights():
        raise NotFound(f"unknown rule: {name}")
    if not isinstance(points, int) or not (0 <= points <= MAX_POINTS):
        raise ValueError(f"points must be a whole number from 0 to {MAX_POINTS} (0 switches the rule off)")
    if points == default_rule_weights()[name]:
        settings_repo.clear([f"rule.{name}"], actor, reason)
    else:
        settings_repo.set_value(f"rule.{name}", str(points), actor, reason)
    _invalidate()


def set_cutoffs(cut: list[int], actor: str, reason: str) -> None:
    cut = validate_cutoffs(cut)
    if cut == default_cutoffs():
        settings_repo.clear(["cutoffs"], actor, reason)
    else:
        settings_repo.set_value("cutoffs", json.dumps(cut), actor, reason)
    _invalidate()


def reset_all(actor: str, reason: str) -> int:
    keys = [f"rule.{n}" for n in default_rule_weights()] + ["cutoffs"]
    n = settings_repo.clear(keys, actor, reason)
    _invalidate()
    return n


def preview(proposed_rules: dict[str, int] | None, proposed_cutoffs: list[int] | None, limit: int = 300) -> dict:
    """Re-score recent stored scans with proposed numbers, without saving anything. Shows what would change."""
    from app.engine.scoring.combiner import combine
    from app.engine.scoring.overrides import apply_overrides
    from app.engine.scoring.rules import evaluate_rules

    weights = {**rule_weights(), **(proposed_rules or {})}
    cut = validate_cutoffs(proposed_cutoffs) if proposed_cutoffs else cutoffs()
    new_bands = bands(cut)

    def band_name(score: int) -> str:
        return next(b["name"] for b in new_bands if b["min"] <= score <= b["max"])

    before: dict[str, int] = {}
    after: dict[str, int] = {}
    changed = []
    rows = scan_repo.recent_results(limit)
    for row in rows:
        features = row["features"]
        hits = evaluate_rules(features, weights)
        score, _ = apply_overrides(combine(sum(h["points"] for h in hits)), features)
        new_band = band_name(score)
        before[row["band"]] = before.get(row["band"], 0) + 1
        after[new_band] = after.get(new_band, 0) + 1
        if new_band != row["band"] or score != row["score"]:
            changed.append({"scan_id": row["scan_id"], "url": row["url"], "old_score": row["score"], "new_score": score,
                            "old_band": row["band"], "new_band": new_band})
    return {"scans_checked": len(rows), "before": before, "after": after,
            "changed_count": len(changed), "changed": changed[:15]}
