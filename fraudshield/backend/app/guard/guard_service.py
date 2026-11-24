# TODO(DELETE LATER - privacy): switched off, nothing routes here any more. Reading WhatsApp / SMS / email messages is a privacy risk. Delete with the other files listed in PRIVACY_DELETE_LATER.md.
"""The defender: check links in incoming SMS / WhatsApp messages for the accounts that watch that number.

Only basic (offline) scans run here: the message sender is untrusted, so the server never opens their links.
Bands high_risk / likely_fraud -> the message is "blocked" (recorded, user emailed and warned on WhatsApp);
suspicious -> "monitor" (recorded, no email); anything else -> "allowed" (recorded so it shows in the history).
Messages without links are ignored and not stored.
"""
import logging

from app.alerts import mailer, whatsapp
from app.guard.link_extractor import extract_links
from app.repositories import device_repo, message_repo, user_repo, visit_repo, wa_link_repo, watch_repo
from app.services.scan_service import scan_url

log = logging.getLogger(__name__)

BLOCK_BANDS = ("high_risk", "likely_fraud")
_ORDER = {"safe": 0, "suspicious": 1, "high_risk": 2, "likely_fraud": 3}


def _scan_links(urls: list[str]) -> list[dict]:
    out = []
    for u in urls:
        try:
            r = scan_url(u, deep=False)  # not tied to the user: the sender is untrusted; the message log holds the link
        except ValueError:
            continue
        out.append({"url": r["url"], "score": r["score"], "band": r["band"], "scan_id": r["scan_id"],
                    "reasons": [x["reason"] for x in r.get("reasons", []) if x.get("points", 0) > 0][:3]})
    return out


def handle_message(channel: str, recipient: str, sender: str, text: str, only_user: str | None = None) -> dict:
    """channel: 'sms' | 'whatsapp'. recipient: E.164 number of the watched phone. only_user: the gateway told us whose
    linked WhatsApp received it, so only that account is checked. Returns a small summary."""
    urls = extract_links(text or "")
    if not urls:
        return {"matched": 0, "links": 0}
    try:
        number = watch_repo.normalize_phone(recipient)
    except ValueError:
        return {"matched": 0, "links": len(urls)}
    owners = watch_repo.owners_of_number(number)
    if only_user is not None:
        owners = [{"user_id": only_user}]
    handled = 0
    seen_users: set[str] = set()
    for owner in owners:
        uid = owner["user_id"]
        if uid in seen_users:
            continue
        seen_users.add(uid)
        links = _scan_links(urls)
        if not links:
            continue
        worst = max(links, key=lambda l: _ORDER.get(l["band"], 0))["band"]
        action = "blocked" if worst in BLOCK_BANDS else ("monitor" if worst == "suspicious" else "allowed")
        visit_repo.add_many(uid, [{"url": l["url"], "host": _host(l["url"]), "score": l["score"], "band": l["band"],
                                   "source": "message"} for l in links])
        emailed = False
        if action == "blocked" and device_repo.get_settings(uid)["alerts_enabled"]:
            emailed = _notify(uid, channel, sender, number, [l for l in links if l["band"] in BLOCK_BANDS], action)
        message_repo.add(uid, channel, sender, number, links, worst, action, emailed)
        handled += 1
    return {"matched": handled, "links": len(urls)}


def _host(url: str) -> str:
    from app.analyzers.url_analyzer.normalizer import normalize
    try:
        return normalize(url).host
    except ValueError:
        return url[:255]


def _notify(uid: str, channel: str, sender: str, number: str, bad: list[dict], action: str) -> bool:
    user = user_repo.get(uid) or {}
    targets = {e for e in watch_repo.emails_for(uid)}
    if user.get("email"):
        targets.add(user["email"])
    subject, body = mailer.render_alert(uid, channel, sender, bad, action)
    sent = False
    for to in sorted(targets):
        sent = mailer.send(to, subject, body) or sent
    if channel == "whatsapp":  # warn on the same chat; no-op unless an Evolution instance is configured
        link = wa_link_repo.get(uid)
        whatsapp.send_text(number, f"Manee warning: a link in a message from {sender} looks dangerous "
                                   f"({bad[0]['url']}). Do not open it.", instance=link["instance"] if link else None)
    return sent
