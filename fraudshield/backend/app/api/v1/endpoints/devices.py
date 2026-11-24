"""Endpoints the browser extension calls with a device token (Authorization: Bearer fsd_...)."""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.analyzers.url_analyzer.normalizer import normalize
from app.repositories import device_repo, visit_repo

router = APIRouter(prefix="/ext")
BANDS = {"safe", "suspicious", "high_risk", "likely_fraud"}


def device_user(authorization: str = Header(default="")) -> str:
    token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    uid = device_repo.user_for_token(token) if token else None
    if uid is None:
        raise HTTPException(status_code=401, detail="Unknown or removed device token.")
    return uid


class Visit(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    score: int = Field(ge=0, le=100)
    level: str = Field(default="low", pattern="^(low|medium|high)$")


class VisitBatch(BaseModel):
    visits: list[Visit] = Field(max_length=100)


_LEVEL_TO_BAND = {"low": "safe", "medium": "suspicious", "high": "high_risk"}


@router.get("/config")
def config(uid: str = Depends(device_user)) -> dict:
    """The extension polls this: should it be active for this account?"""
    return {"enabled": device_repo.get_settings(uid)["extension_enabled"]}


@router.post("/visits")
def upload_visits(body: VisitBatch, uid: str = Depends(device_user)) -> dict:
    if not device_repo.get_settings(uid)["extension_enabled"]:
        return {"stored": 0, "enabled": False}
    items = []
    for v in body.visits:
        try:
            host = normalize(v.url).host
        except ValueError:
            continue
        band = "likely_fraud" if v.score >= 80 else _LEVEL_TO_BAND[v.level]
        items.append({"url": v.url, "host": host, "score": v.score, "band": band, "source": "extension"})
    return {"stored": visit_repo.add_many(uid, items) if items else 0, "enabled": True}
