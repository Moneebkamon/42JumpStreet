"""Decide whether a detection deserves an alert and send it. Off unless both Telegram env vars are set."""
import os
from collections.abc import Callable

from app.alerts.telegram import send_message

ALERT_BANDS = {"high_risk", "likely_fraud"}


def alerts_configured() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def format_alert(det: dict) -> str:
    tag = "[SIMULATED] " if det.get("simulated") else ""
    top = "; ".join(r["reason"] for r in det["reasons"][:3])
    brand = f" | impersonating {det['brand_name']}" if det.get("brand_name") else ""
    return (
        f"{tag}Manee: suspected scam domain\n{det['domain']}\n"
        f"Score {det['score']} ({det['band']}){brand}\nWhy: {top}"
    )


def notify(det: dict, sender: Callable[[str, str, str], bool] = send_message) -> bool:
    """Alert for high-risk detections only. Returns True if a message was sent."""
    if det["band"] not in ALERT_BANDS or not alerts_configured():
        return False
    return sender(format_alert(det), os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"])
