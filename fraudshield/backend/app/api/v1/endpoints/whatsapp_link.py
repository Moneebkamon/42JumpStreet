"""Link a member's WhatsApp from the website: enter the number, scan the QR code, done. The gateway key never leaves the server."""
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.alerts import whatsapp
from app.api.deps import require_user
from app.repositories import wa_link_repo, watch_repo
from app.services import audit_service

router = APIRouter(prefix="/me/whatsapp")


class ConnectBody(BaseModel):
    number: str = Field(min_length=5, max_length=30)


def _max_links() -> int:
    return int(os.environ.get("MANEE_MAX_WA_LINKS", "20"))


def _view(link: dict | None, status: str | None = None, qr: str | None = None, pairing_code: str | None = None) -> dict:
    return {"available": whatsapp.configured(), "linked": bool(link) and (status or link["status"]) == "open",
            "status": (status or (link or {}).get("status") or "none"), "number": (link or {}).get("number"),
            "qr": qr, "pairing_code": pairing_code}


@router.post("/connect")
def connect(body: ConnectBody, user: tuple[str, str] = Depends(require_user)) -> dict:
    uid = user[0]
    if not whatsapp.configured():
        raise HTTPException(status_code=503, detail="WhatsApp linking is not set up on this server.")
    try:
        number = watch_repo.normalize_phone(body.number)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    existing = wa_link_repo.get(uid)
    if not existing and wa_link_repo.count() >= _max_links():
        raise HTTPException(status_code=429, detail="WhatsApp linking is full right now. Try again later.")
    inst = wa_link_repo.instance_name(uid)
    try:
        whatsapp.create_instance(inst)
        whatsapp.set_webhook(inst)
        if whatsapp.state(inst) == "open" and existing and existing["number"] == number:
            wa_link_repo.set_status(uid, "open")
            return _view(wa_link_repo.get(uid), "open")
        link = wa_link_repo.upsert(uid, number)
        code = whatsapp.connect(inst, number)
    except whatsapp.EvolutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    try:  # the number joins the watch list so its messages are checked for this account
        watch_repo.add(uid, "whatsapp", number)
    except ValueError:
        pass
    audit_service.record(uid, "whatsapp.link_started", "user", uid)
    return _view(link, "connecting", code["qr"], code["pairing_code"])


@router.get("/status")
def status(user: tuple[str, str] = Depends(require_user)) -> dict:
    link = wa_link_repo.get(user[0])
    if not link or not whatsapp.configured():
        return _view(link)
    try:
        st = whatsapp.state(link["instance"])
    except whatsapp.EvolutionError:
        return _view(link)
    if st == "missing":
        wa_link_repo.delete(user[0])
        return _view(None)
    new = "open" if st == "open" else "connecting"
    if new != link["status"]:
        wa_link_repo.set_status(user[0], new)
    return _view(link, new)


@router.post("/refresh")
def refresh_qr(user: tuple[str, str] = Depends(require_user)) -> dict:
    """QR codes expire after about a minute; ask for a new one."""
    link = wa_link_repo.get(user[0])
    if not link:
        raise HTTPException(status_code=404, detail="Start the connection first.")
    try:
        code = whatsapp.connect(link["instance"], link["number"])
    except whatsapp.EvolutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _view(link, "connecting", code["qr"], code["pairing_code"])


@router.delete("")
def disconnect(user: tuple[str, str] = Depends(require_user)) -> dict:
    link = wa_link_repo.get(user[0])
    if link:
        try:
            whatsapp.delete_instance(link["instance"])
        except whatsapp.EvolutionError:
            pass  # forget it on our side anyway; the user can retry from a clean state
        wa_link_repo.delete(user[0])
        audit_service.record(user[0], "whatsapp.unlinked", "user", user[0])
    return _view(None)
