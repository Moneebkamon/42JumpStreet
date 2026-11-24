"""Everything a signed-in account manages about itself: switches, history, watched contacts, alerts, linked devices."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import require_user
from app.repositories import device_repo, message_repo, scan_repo, visit_repo, watch_repo

router = APIRouter(prefix="/me")


class SettingsBody(BaseModel):
    extension_enabled: bool | None = None
    alerts_enabled: bool | None = None


class ContactBody(BaseModel):
    kind: str = Field(pattern="^(email|phone|whatsapp)$")
    value: str = Field(min_length=3, max_length=200)


class DeviceBody(BaseModel):
    label: str = Field(default="Chrome", max_length=60)


@router.get("/summary")
def summary(user: tuple[str, str] = Depends(require_user)) -> dict:
    uid = user[0]
    scans = scan_repo.list_recent(limit=200, user_id=uid)
    return {
        "username": uid,
        "role": user[1],
        "settings": device_repo.get_settings(uid),
        "scans": len(scans),
        "risky_scans": sum(1 for s in scans if s["score"] >= 60),
        **visit_repo.counts(uid),
        **message_repo.counts(uid),
        "contacts": len(watch_repo.list_for(uid)),
        "devices": len(device_repo.list_for(uid)),
    }


@router.get("/settings")
def get_settings(user: tuple[str, str] = Depends(require_user)) -> dict:
    return device_repo.get_settings(user[0])


@router.put("/settings")
def put_settings(body: SettingsBody, user: tuple[str, str] = Depends(require_user)) -> dict:
    return device_repo.set_settings(user[0], body.extension_enabled, body.alerts_enabled)


@router.get("/history")
def history(
    limit: int = Query(100, ge=1, le=300),
    source: str | None = Query(None, pattern="^(extension|message|manual)$"),
    band: str | None = Query(None, pattern="^(safe|suspicious|high_risk|likely_fraud)$"),
    user: tuple[str, str] = Depends(require_user),
) -> list[dict]:
    """Links the account researched (manual checks) or visited (extension, messages), newest first."""
    uid, items = user[0], []
    if source in (None, "manual"):
        for s in scan_repo.list_recent(limit=limit, user_id=uid):
            if band is None or s["band"] == band:
                items.append({"url": s["url"], "score": s["score"], "band": s["band"], "source": "manual",
                              "created_at": s["created_at"], "scan_id": s["scan_id"], "deep": s["deep"]})
    if source != "manual":
        for v in visit_repo.list_for(uid, limit=limit, source=source, band=band):
            items.append({**v, "scan_id": None, "deep": False})
    items.sort(key=lambda i: i["created_at"], reverse=True)
    return items[:limit]


@router.delete("/history")
def clear_history(user: tuple[str, str] = Depends(require_user)) -> dict:
    return {"deleted": scan_repo.delete_for_user(user[0]) + visit_repo.delete_for_user(user[0])}


# TODO(DELETE LATER - privacy): the watch list of phone numbers / emails and the message alerts only existed to check
# incoming WhatsApp / SMS / email messages, which is switched off.
# @router.get("/contacts")
# def list_contacts(user: tuple[str, str] = Depends(require_user)) -> list[dict]:
#     return watch_repo.list_for(user[0])
#
#
# @router.post("/contacts", status_code=201)
# def add_contact(body: ContactBody, user: tuple[str, str] = Depends(require_user)) -> dict:
#     try:
#         return watch_repo.add(user[0], body.kind, body.value)
#     except ValueError as exc:
#         raise HTTPException(status_code=422, detail=str(exc)) from exc
#
#
# @router.delete("/contacts/{contact_id}")
# def delete_contact(contact_id: int, user: tuple[str, str] = Depends(require_user)) -> dict:
#     if not watch_repo.remove(user[0], contact_id):
#         raise HTTPException(status_code=404, detail="contact not found")
#     return {"ok": True}
#
#
# @router.get("/alerts")
# def alerts(limit: int = Query(50, ge=1, le=200), user: tuple[str, str] = Depends(require_user)) -> list[dict]:
#     return message_repo.list_for(user[0], limit=limit)


@router.get("/devices")
def list_devices(user: tuple[str, str] = Depends(require_user)) -> list[dict]:
    return device_repo.list_for(user[0])


@router.post("/devices", status_code=201)
def link_device(body: DeviceBody, user: tuple[str, str] = Depends(require_user)) -> dict:
    """Create a token to paste into the extension. It is shown once."""
    try:
        device_id, token = device_repo.create(user[0], body.label.strip())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": device_id, "token": token}


@router.delete("/devices/{device_id}")
def unlink_device(device_id: int, user: tuple[str, str] = Depends(require_user)) -> dict:
    if not device_repo.remove(user[0], device_id):
        raise HTTPException(status_code=404, detail="device not found")
    return {"ok": True}
