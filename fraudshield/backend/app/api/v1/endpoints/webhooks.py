"""Inbound message webhooks: WhatsApp (Evolution API) and SMS (Twilio-style). Both are guarded by a shared secret.

Set FRAUDSHIELD_WEBHOOK_SECRET, then give the provider a URL that carries it, either as the header X-Webhook-Secret or
as ?secret=... (Twilio cannot add headers). With no secret set the endpoints refuse everything.
"""
import hmac
import os
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import client_key
from app.core.rate_limit import SlidingWindowLimiter
from app.guard import bot_service
from app.guard.guard_service import handle_message
from app.repositories import wa_link_repo

router = APIRouter(prefix="/webhooks")
limiter = SlidingWindowLimiter(max_hits=120, window_seconds=60)
MAX_BODY = 64 * 1024


def _check(request: Request) -> None:
    secret = os.environ.get("FRAUDSHIELD_WEBHOOK_SECRET", "")
    given = request.headers.get("x-webhook-secret") or request.query_params.get("secret") or ""
    if not secret or not hmac.compare_digest(given.encode(), secret.encode()):
        raise HTTPException(status_code=401, detail="bad webhook secret")
    if os.environ.get("FRAUDSHIELD_RATE_LIMIT", "1") != "0" and not limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="slow down")


async def _body(request: Request) -> bytes:
    raw = await request.body()
    if len(raw) > MAX_BODY:
        raise HTTPException(status_code=413, detail="payload too large")
    return raw


def _jid_number(jid: str) -> str:
    return "+" + jid.split("@")[0].split(":")[0] if jid else ""


def parse_evolution(payload: dict) -> list[tuple[str, str, str]]:
    """(recipient_number, sender_label, text) for each incoming message in an Evolution messages.upsert payload.
    The recipient is the number the instance is connected to (top-level `sender`), i.e. the watched phone."""
    event = str(payload.get("event", "")).lower().replace("_", ".")
    if event and event != "messages.upsert":
        return []
    data = payload.get("data") or {}
    items = data if isinstance(data, list) else [data]
    out = []
    for d in items:
        key = d.get("key") or {}
        if key.get("fromMe") or "@g.us" in str(key.get("remoteJid", "")):
            continue
        msg = d.get("message") or {}
        text = msg.get("conversation") or (msg.get("extendedTextMessage") or {}).get("text") or ""
        recipient = _jid_number(str(payload.get("sender", "")))
        if text:  # recipient may be empty: the caller then relies on the instance name
            out.append((recipient, _jid_number(str(key.get("remoteJid", ""))) or "unknown", text))
    return out


def _bot(payload: dict) -> int:
    """Manee's own number: reply to whoever wrote to it (a forwarded message, or a pasted link)."""
    event = str(payload.get("event", "")).lower().replace("_", ".")
    if event and event != "messages.upsert":
        return 0
    data = payload.get("data") or {}
    n = 0
    for d in data if isinstance(data, list) else [data]:
        key = d.get("key") or {}
        jid = str(key.get("remoteJidAlt") or key.get("remoteJid") or "")
        if key.get("fromMe") or "@g.us" in jid or "@broadcast" in jid or not jid:
            continue
        msg = d.get("message") or {}
        text = msg.get("conversation") or (msg.get("extendedTextMessage") or {}).get("text") or ""
        if text and bot_service.handle(jid, text):
            n += 1
    return n


@router.post("/whatsapp")
async def whatsapp(request: Request) -> dict:
    _check(request)
    raw = await _body(request)
    try:
        import json
        payload = json.loads(raw or b"{}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="invalid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="invalid payload")
    if str(payload.get("instance", "")) == bot_service.bot_instance():
        return {"ok": True, "handled": _bot(payload)}
    link = wa_link_repo.get_by_instance(str(payload.get("instance", ""))) if payload.get("instance") else None
    handled = 0
    for rec, snd, txt in parse_evolution(payload):
        if link:  # the gateway names the instance, so we know exactly whose WhatsApp received it
            handled += handle_message("whatsapp", link["number"], snd, txt, only_user=link["user_id"])["matched"]
        else:
            handled += handle_message("whatsapp", rec, snd, txt)["matched"]
    return {"ok": True, "handled": handled}


@router.post("/sms")
async def sms(request: Request) -> dict:
    _check(request)
    form = parse_qs((await _body(request)).decode("utf-8", "replace"))
    first = lambda k: (form.get(k) or [""])[0]  # noqa: E731
    result = handle_message("sms", first("To"), first("From") or "unknown", first("Body"))
    return {"ok": True, "handled": result["matched"]}
