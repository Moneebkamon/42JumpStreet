import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import client_key, current_user, is_staff
from app.core.auth import auth_enabled
from app.core.errors import RateLimited
from app.core.rate_limit import SlidingWindowLimiter
from app.engine.explainer import explain
from app.repositories import scan_repo
from app.schemas.scan import FeedbackRequest, ScanRequest, ScanResponse, ScanSummary, StoredScan
from app.services.scan_service import scan_url

router = APIRouter()

# Per client, in memory (this process only). FRAUDSHIELD_RATE_LIMIT=0 switches them off (tests, local load checks).
scan_limiter = SlidingWindowLimiter(max_hits=60, window_seconds=60)
deep_limiter = SlidingWindowLimiter(max_hits=5, window_seconds=60)


def _limits_on() -> bool:
    return os.environ.get("FRAUDSHIELD_RATE_LIMIT", "1") != "0"


@router.post("/scan", response_model=ScanResponse)
def create_scan(body: ScanRequest, request: Request, user: tuple[str, str] | None = Depends(current_user)) -> dict:
    """Public for link checks. Opening the page in the safe browser (deep) is for signed-in staff only: it makes this
    server contact the link, so anyone being able to trigger it would be an abuse risk. This build is a demo: deep scan
    is meant for the staged test pages, not for real scam sites (see docs/sandbox.md)."""
    if body.deep and auth_enabled():
        if user is None:
            raise HTTPException(status_code=401, detail="Opening the page in the safe browser is for signed-in staff.")
        if not is_staff(user):
            raise HTTPException(status_code=403, detail="Deep search is for staff accounts.")
    if _limits_on():
        who = user[0] if user else client_key(request)
        if not scan_limiter.allow(f"scan:{who}"):
            raise RateLimited("Too many scans from your connection. Please wait a minute.")
        if body.deep and not deep_limiter.allow(f"deep:{who}"):
            raise RateLimited("Too many safe-browser scans. Please wait a minute.")
    try:
        return scan_url(body.url, deep=body.deep, user_id=user[0] if user else None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/scans", response_model=list[ScanSummary])
def list_scans(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    min_score: int = Query(0, ge=0, le=100),
    user: tuple[str, str] | None = Depends(current_user),
) -> list[dict]:
    """Scan history, newest first. Staff see all scans, a regular user only their own, visitors none."""
    if is_staff(user):
        return scan_repo.list_recent(limit=limit, offset=offset, min_score=min_score)
    if user is None:
        return []
    return scan_repo.list_recent(limit=limit, offset=offset, min_score=min_score, user_id=user[0])


def _check_access(scan_id: str, user: tuple[str, str] | None) -> None:
    """Scans made without an account are reachable by their (unguessable) id; owned scans only by owner or staff."""
    exists, owner = scan_repo.owner(scan_id)
    if not exists:
        raise HTTPException(status_code=404, detail="scan not found")
    if owner is not None and not is_staff(user) and (user is None or user[0] != owner):
        raise HTTPException(status_code=404, detail="scan not found")


@router.get("/scan/{scan_id}", response_model=StoredScan)
def get_scan(scan_id: str, user: tuple[str, str] | None = Depends(current_user)) -> dict:
    _check_access(scan_id, user)
    found = scan_repo.get(scan_id)
    if found is None:
        raise HTTPException(status_code=404, detail="scan not found")
    found.setdefault("explanation", "")
    if not found["explanation"]:  # scans stored before explanations existed
        found["explanation"] = explain(found)
    return found


@router.post("/scan/{scan_id}/feedback")
def give_feedback(scan_id: str, body: FeedbackRequest, user: tuple[str, str] | None = Depends(current_user)) -> dict:
    """Record a human verdict on a scan. These become labels for calibrating the scorer later."""
    _check_access(scan_id, user)
    if not scan_repo.set_feedback(scan_id, body.label):
        raise HTTPException(status_code=404, detail="scan not found")
    return {"scan_id": scan_id, "feedback": body.label}
