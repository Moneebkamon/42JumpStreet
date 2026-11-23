from fastapi import APIRouter, Query

from app.discovery import domain_watch
from app.schemas.feed import CheckedItem, DiscoveryStats

router = APIRouter()


@router.get("/stats", response_model=DiscoveryStats)
def get_stats() -> dict:
    """Discovery figures: pass-through rate, flagged count, processing and issue-to-detection time."""
    return domain_watch.stats()


@router.get("/checked", response_model=list[CheckedItem])
def get_checked(limit: int = Query(300, ge=1, le=1000)) -> list[dict]:
    """The most recently checked domains (newest first), including the ones the name check passed over."""
    return domain_watch.recent_checked(limit)
