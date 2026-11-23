"""Send one message through the Telegram Bot API. Network code lives only here."""
import httpx


def send_message(text: str, token: str, chat_id: str, post=httpx.post) -> bool:
    """True if Telegram accepted the message. Never raises: an alert failing must not stop discovery."""
    try:
        resp = post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False
