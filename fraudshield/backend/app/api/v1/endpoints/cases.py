from fastapi import APIRouter, Depends, Query

from app.api.deps import get_actor
from app.repositories import case_repo
from app.schemas.case import CaseCreate, NoteCreate, StatusChange
from app.services import case_service, priority_service

router = APIRouter()


@router.get("/queue")
def triage_queue(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    """Detections and citizen reports with no case yet, highest priority first."""
    return priority_service.triage_queue(limit)


@router.get("/cases")
def list_cases(status: str | None = None, limit: int = Query(100, ge=1, le=200)) -> list[dict]:
    return case_repo.list_cases(status=status, limit=limit)


@router.post("/cases", status_code=201)
def create_case(body: CaseCreate, actor: str = Depends(get_actor)) -> dict:
    return case_service.create_case(body.source, body.source_ref, actor, body.title)


@router.get("/cases/{ref}")
def get_case(ref: str) -> dict:
    return case_service.case_detail(ref)


@router.patch("/cases/{ref}")
def change_status(ref: str, body: StatusChange, actor: str = Depends(get_actor)) -> dict:
    return case_service.change_status(ref, body.to_status, body.reason, actor)


@router.post("/cases/{ref}/notes", status_code=201)
def add_note(ref: str, body: NoteCreate, actor: str = Depends(get_actor)) -> dict:
    return case_service.add_note(ref, body.text, actor)
