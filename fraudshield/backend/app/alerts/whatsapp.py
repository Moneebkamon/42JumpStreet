# TODO(DELETE LATER - privacy): switched off, nothing routes here any more. Reading WhatsApp / SMS / email messages is a privacy risk. Delete with the other files listed in PRIVACY_DELETE_LATER.md.
"""Manee's WhatsApp gateway client (Evolution API v2, run from infra/evolution). One instance per linked user.

Environment (all optional; with no EVOLUTION_API_KEY WhatsApp linking is simply unavailable):
  EVOLUTION_API_URL   where the gateway is reachable from the backend (default http://localhost:8081)
  EVOLUTION_API_KEY   the gateway's key. Stays on the server, never sent to the browser.
  MANEE_WEBHOOK_BASE  where the gateway reaches this backend (default http://host.docker.internal:8000)
  FRAUDSHIELD_WEBHOOK_SECRET  sent by the gateway with every webhook call
The send call is the one the uptime-kuma "evolution" provider makes: POST {number, text} to /message/sendText/<instance>.
"""
import logging
import os

import httpx

log = logging.getLogger(__name__)
TIMEOUT = 15


class EvolutionError(Exception):
    """The gateway is unconfigured, unreachable or refused the call. The message is safe to show to a user."""


def _base() -> str:
    return os.environ.get("EVOLUTION_API_URL", "http://localhost:8081").rstrip("/")


def configured() -> bool:
    return bool(os.environ.get("EVOLUTION_API_KEY"))


def _call(method: str, path: str, json: dict | None = None, ok_missing: bool = False) -> dict:
    if not configured():
        raise EvolutionError("WhatsApp linking is not set up on this server.")
    try:
        r = httpx.request(method, f"{_base()}{path}", json=json, headers={"apikey": os.environ["EVOLUTION_API_KEY"]}, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        log.warning("evolution unreachable: %s", exc)
        raise EvolutionError("The WhatsApp gateway is not reachable. Try again in a moment.") from exc
    if r.status_code == 404 and ok_missing:
        return {}
    if r.status_code >= 300:
        log.warning("evolution %s %s -> %s %s", method, path, r.status_code, r.text[:200])
        raise EvolutionError("The WhatsApp gateway refused the request.")
    try:
        data = r.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def create_instance(instance: str) -> None:
    """Idempotent: an already existing instance is fine."""
    try:
        _call("POST", "/instance/create", {"instanceName": instance, "qrcode": True, "integration": "WHATSAPP-BAILEYS"})
    except EvolutionError:
        if state(instance) == "missing":
            raise


def set_webhook(instance: str) -> None:
    base = os.environ.get("MANEE_WEBHOOK_BASE", "http://host.docker.internal:8000").rstrip("/")
    _call("POST", f"/webhook/set/{instance}", {"webhook": {
        "enabled": True,
        "url": f"{base}/api/v1/webhooks/whatsapp",
        "byEvents": False,
        "base64": False,
        "headers": {"X-Webhook-Secret": os.environ.get("FRAUDSHIELD_WEBHOOK_SECRET", ""), "Content-Type": "application/json"},
        "events": ["MESSAGES_UPSERT"],
    }})


def connect(instance: str, number: str | None = None) -> dict:
    """Ask for a fresh QR code. Returns {qr: data-URL|None, pairing_code: str|None}. `number` (digits) also yields a pairing code."""
    path = f"/instance/connect/{instance}" + (f"?number={number.lstrip('+')}" if number else "")
    data = _call("GET", path)
    qr = data.get("base64") or (data.get("qrcode") or {}).get("base64")
    if isinstance(qr, str) and qr and not qr.startswith("data:"):
        qr = "data:image/png;base64," + qr
    return {"qr": qr or None, "pairing_code": data.get("pairingCode") or (data.get("qrcode") or {}).get("pairingCode")}


def state(instance: str) -> str:
    """'open' (linked), 'connecting', 'close' or 'missing'."""
    data = _call("GET", f"/instance/connectionState/{instance}", ok_missing=True)
    if not data:
        return "missing"
    return str((data.get("instance") or data).get("state") or "close")


def delete_instance(instance: str) -> None:
    _call("DELETE", f"/instance/logout/{instance}", ok_missing=True)
    _call("DELETE", f"/instance/delete/{instance}", ok_missing=True)


def send_text(number: str, text: str, instance: str | None = None) -> bool:
    """Warn someone on WhatsApp through `instance` (default env EVOLUTION_INSTANCE). Never raises."""
    instance = instance or os.environ.get("EVOLUTION_INSTANCE")
    if not configured() or not instance:
        return False
    try:
        _call("POST", f"/message/sendText/{instance}", {"number": number.lstrip("+"), "text": text})
        return True
    except EvolutionError:
        return False
