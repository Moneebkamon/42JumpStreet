from fastapi import APIRouter, Depends

from app.api.deps import get_actor
from app.services import evidence_service

router = APIRouter()


@router.post("/cases/{ref}/evidence", status_code=201)
def freeze_evidence(ref: str, actor: str = Depends(get_actor)) -> list[dict]:
    """Freeze and hash the analysis the case is built on. Returns the items (metadata only)."""
    return evidence_service.freeze(ref, actor)


@router.get("/evidence/{evidence_id}")
def view_evidence(evidence_id: int, actor: str = Depends(get_actor)) -> dict:
    return evidence_service.get_evidence(evidence_id, actor)


@router.get("/evidence/{evidence_id}/verify")
def verify_evidence(evidence_id: int, actor: str = Depends(get_actor)) -> dict:
    return evidence_service.verify(evidence_id, actor)
