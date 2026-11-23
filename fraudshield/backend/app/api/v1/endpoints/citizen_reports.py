from fastapi import APIRouter, Request

from app.api.deps import client_key
from app.repositories import citizen_report_repo
from app.schemas.citizen_report import CitizenReportCreate
from app.services import citizen_report_service

public_router = APIRouter()  # anyone may report
staff_router = APIRouter()  # only staff may read reports


@public_router.post("/citizen-reports", status_code=201)
def submit_report(body: CitizenReportCreate, request: Request) -> dict:
    """Public. The reported page is never opened; the link is scored from its text and domain."""
    return citizen_report_service.submit(body.url, body.note, body.contact, body.website, client_key(request))


@staff_router.get("/citizen-reports")
def list_reports(limit: int = 100) -> list[dict]:
    return citizen_report_repo.list_recent(min(max(limit, 1), 200))
