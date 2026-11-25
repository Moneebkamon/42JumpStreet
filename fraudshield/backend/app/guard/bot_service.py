"""The Manee WhatsApp bot: anyone can forward a suspicious message (or paste a link) to Manee's own number and get a
verdict back in the same chat. Nothing is linked and nothing outside what the sender chose to send is read.

Only the link and verdict are kept (in the scan history); the message text is never stored. The links are scanned
offline (the page is never opened). Set MANEE_BOT_INSTANCE to the gateway instance that holds Manee's number.
"""
import logging
import os
import re

from app.alerts import whatsapp
from app.core.rate_limit import SlidingWindowLimiter
from app.guard.guard_service import _scan_links
from app.guard.link_extractor import extract_links

log = logging.getLogger(__name__)
limiter = SlidingWindowLimiter(max_hits=10, window_seconds=60)
notice_limiter = SlidingWindowLimiter(max_hits=1, window_seconds=60)  # tell a flooder once per minute, then stay quiet
_ARABIC = re.compile(r"[؀-ۿ]")

_BAND = {  # band -> (emoji, English label, Arabic label)
    "likely_fraud": ("🔴", "Likely fraud", "احتيال مرجّح"),
    "high_risk": ("🟠", "High risk", "خطر مرتفع"),
    "suspicious": ("🟡", "Suspicious", "مشبوه"),
    "safe": ("🟢", "No warning signs found", "لا توجد مؤشرات خطر"),
}
_TEXT = {
    "en": {"none": "Send me a link, or forward a message that has one, and I will check it for you.",
           "slow": "Too many requests. Please wait a minute and try again.",
           "bad": "Do NOT open it. Do not share codes or card details.",
           "ok": "No warning signs found, but this is not a guarantee. Be careful with links you did not expect.",
           "mid": "Be careful. Do not enter passwords or card details.",
           "foot": "Manee checks the link text only, it never opens the page."},
    "ar": {"none": "أرسل لي رابطاً أو أعد توجيه رسالة تحتوي رابطاً وسأفحصه لك.",
           "slow": "طلبات كثيرة. انتظر دقيقة ثم حاول مجدداً.",
           "bad": "لا تفتح الرابط. لا تشارك أي رموز أو بيانات بطاقة.",
           "ok": "لم نجد مؤشرات خطر، لكن هذا ليس ضماناً. احذر من الروابط غير المتوقعة.",
           "mid": "احذر. لا تدخل كلمات مرور أو بيانات بطاقة.",
           "foot": "يفحص منيع نص الرابط فقط ولا يفتح الصفحة."},
}


def bot_instance() -> str:
    return os.environ.get("MANEE_BOT_INSTANCE", "Manee")


def build_reply(text: str, links: list[dict]) -> str:
    lang = "ar" if _ARABIC.search(text or "") else "en"
    tx = _TEXT[lang]
    if not links:
        return tx["none"]
    order = ["safe", "suspicious", "high_risk", "likely_fraud"]
    worst = max(links, key=lambda l: order.index(l["band"]) if l["band"] in order else 0)["band"]
    lines = []
    for l in links:
        emoji, en, ar = _BAND.get(l["band"], _BAND["suspicious"])
        lines.append(f"{emoji} {ar if lang == 'ar' else en} ({l['score']}/100)\n{l['url']}")
        for r in l.get("reasons", [])[:3]:
            lines.append(f"  • {r}")
    advice = tx["bad"] if worst in ("high_risk", "likely_fraud") else (tx["mid"] if worst == "suspicious" else tx["ok"])
    return "\n".join(lines) + f"\n\n{advice}\n\n_{tx['foot']}_"


def handle(sender_jid: str, text: str) -> bool:
    """Check the links in `text` and reply to `sender_jid`. Returns True if a reply was sent."""
    if not sender_jid:
        return False
    if not limiter.allow(sender_jid):
        return whatsapp.send_text(sender_jid, _TEXT["ar" if _ARABIC.search(text or "") else "en"]["slow"], instance=bot_instance()) \
            if notice_limiter.allow(sender_jid) else False
    links = _scan_links(extract_links(text or ""))
    return whatsapp.send_text(sender_jid, build_reply(text, links), instance=bot_instance())
