from fastapi import APIRouter, Query

from app.services import audit_service

router = APIRouter()


@router.get("/audit")
def audit_log(
    limit: int = Query(100, ge=1, le=500), object_type: str | None = None, object_id: str | None = None
) -> list[dict]:
    """Who did what and when (newest first)."""
    return audit_service.recent(limit, object_type, object_id)
