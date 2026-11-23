from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.api.deps import get_actor
from app.core.errors import NotFound
from app.repositories import action_repo
from app.schemas.takedown import DraftCreate
from app.services import takedown_service

router = APIRouter()


@router.get("/takedown-recipients")
def recipients() -> dict:
    return takedown_service.RECIPIENTS


@router.post("/cases/{ref}/takedown-drafts", status_code=201)
def create_draft(ref: str, body: DraftCreate, actor: str = Depends(get_actor)) -> dict:
    """Draft a report for a recipient type. Drafts are never sent by the system."""
    return takedown_service.build_draft(ref, body.recipient_type, actor)


@router.get("/takedowns/{draft_id}")
def get_draft(draft_id: int) -> dict:
    draft = action_repo.get_draft(draft_id)
    if not draft:
        raise NotFound(f"draft {draft_id} not found")
    return draft


@router.get("/takedowns/{draft_id}/export", response_class=PlainTextResponse)
def export_draft(draft_id: int, actor: str = Depends(get_actor)) -> PlainTextResponse:
    filename, text = takedown_service.export(draft_id, actor)
    return PlainTextResponse(text, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
