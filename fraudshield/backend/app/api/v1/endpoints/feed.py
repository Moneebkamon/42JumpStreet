from fastapi import APIRouter, Query

from app.discovery import domain_watch
from app.engine.prioritizer import prioritize
from app.schemas.feed import FeedItem, TriageItem

router = APIRouter()


@router.get("/feed", response_model=list[FeedItem])
def get_feed(
    min_score: int = Query(0, ge=0, le=100),
    brand: str | None = None,
    source: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """Latest domains found by proactive discovery, newest first."""
    return domain_watch.list_detections(min_score=min_score, brand=brand, source=source, status=status, limit=limit)


@router.get("/triage", response_model=list[TriageItem])
def get_triage(budget_seconds: float = Query(60, gt=0, le=3600)) -> list[dict]:
    """Recommend which detections deserve a deeper look first within a time budget.

    Recommendation only: nothing is fetched or scanned by this call.
    """
    pool = domain_watch.list_detections(min_score=1, limit=200)
    return prioritize(pool, budget_seconds)
