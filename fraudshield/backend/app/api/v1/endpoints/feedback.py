"""Admin: the false-positive review queue and the allowlist. Admin role only."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_actor
from app.repositories import allowlist_repo
from app.services import feedback_service

router = APIRouter(prefix="/admin")


class Decision(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


@router.get("/feedback")
def review_queue() -> list[dict]:
    """Links we flagged that a person marked as safe and nobody has reviewed yet."""
    return feedback_service.queue()


@router.post("/feedback/{scan_id}/promote")
def promote(scan_id: str, body: Decision, actor: str = Depends(get_actor)) -> dict:
    return feedback_service.promote(scan_id, body.reason.strip(), actor)


@router.post("/feedback/{scan_id}/dismiss")
def dismiss(scan_id: str, body: Decision, actor: str = Depends(get_actor)) -> dict:
    return feedback_service.dismiss(scan_id, body.reason.strip(), actor)


@router.get("/allowlist")
def allowlist() -> list[dict]:
    return allowlist_repo.list_all()


@router.delete("/allowlist/{host}")
def remove_from_allowlist(host: str, reason: str = "removed by an administrator", actor: str = Depends(get_actor)) -> dict:
    feedback_service.remove(host, actor, reason)
    return {"host": host, "removed": True}
