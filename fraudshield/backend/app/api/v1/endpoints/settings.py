"""Admin: view and change rule points and risk-band cutoffs, preview a change, see the change history. Admin role only."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_actor
from app.core.errors import NotFound
from app.engine.scoring import tuning
from app.engine.scoring.rules import RULES
from app.repositories import settings_repo
from app.services import audit_service

router = APIRouter(prefix="/admin/settings")


class RuleChange(BaseModel):
    points: int
    reason: str = Field(min_length=3, max_length=500)


class CutoffChange(BaseModel):
    suspicious: int
    high_risk: int
    likely_fraud: int
    reason: str = Field(min_length=3, max_length=500)


class Reset(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class Preview(BaseModel):
    rules: dict[str, int] = {}
    cutoffs: list[int] | None = None


def _view() -> dict:
    current, default = tuning.rule_weights(), tuning.default_rule_weights()
    return {
        "max_points": tuning.MAX_POINTS,
        "rules": [{"name": n, "default": default[n], "current": current[n], "changed": current[n] != default[n],
                   "implemented": n in RULES} for n in default],
        "cutoffs": {"current": tuning.cutoffs(), "default": tuning.default_cutoffs()},
        "bands": tuning.bands(),
        "history": settings_repo.history(30),
    }


@router.get("")
def get_settings() -> dict:
    return _view()


@router.put("/rules/{name}")
def set_rule(name: str, body: RuleChange, actor: str = Depends(get_actor)) -> dict:
    old = tuning.rule_weights().get(name)
    tuning.set_rule(name, body.points, actor, body.reason.strip())  # NotFound -> 404, ValueError -> 422
    audit_service.record(actor, "settings.rule", "rule", name, f"{old} -> {body.points}: {body.reason.strip()}")
    return _view()


@router.put("/cutoffs")
def set_cutoffs(body: CutoffChange, actor: str = Depends(get_actor)) -> dict:
    new = [body.suspicious, body.high_risk, body.likely_fraud]
    old = tuning.cutoffs()
    tuning.set_cutoffs(new, actor, body.reason.strip())
    audit_service.record(actor, "settings.cutoffs", "bands", "cutoffs", f"{old} -> {new}: {body.reason.strip()}")
    return _view()


@router.post("/reset")
def reset(body: Reset, actor: str = Depends(get_actor)) -> dict:
    n = tuning.reset_all(actor, body.reason.strip())
    audit_service.record(actor, "settings.reset", "settings", "all", f"{n} override(s) removed: {body.reason.strip()}")
    return _view()


@router.post("/preview")
def preview(body: Preview, limit: int = Query(300, ge=1, le=1000)) -> dict:
    """Re-score recent stored scans with proposed numbers. Saves nothing."""
    for name, pts in body.rules.items():
        if name not in tuning.default_rule_weights():
            raise NotFound(f"unknown rule: {name}")
        if not (0 <= pts <= tuning.MAX_POINTS):
            raise ValueError(f"points must be from 0 to {tuning.MAX_POINTS}")
    return tuning.preview(body.rules, body.cutoffs, limit)
