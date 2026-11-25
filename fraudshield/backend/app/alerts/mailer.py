"""Send alert emails. Never raises: a mail problem must not break message checking.

Logic follows the user's beyin-dev email-sender (severity-coloured dark HTML, escaped text, SMTP delivery) but no keys,
hosts or addresses are copied. Everything comes from the environment:
  FRAUDSHIELD_SMTP_HOST, FRAUDSHIELD_SMTP_PORT (default 587), FRAUDSHIELD_SMTP_USER, FRAUDSHIELD_SMTP_PASSWORD,
  FRAUDSHIELD_MAIL_FROM, FRAUDSHIELD_SMTP_SSL=1 for implicit TLS (port 465).
With no SMTP host set (dev/test), each email is written as an .html file in the outbox folder
(FRAUDSHIELD_OUTBOX, default data/interim/outbox) so it can be opened in a browser.
"""
import html
import logging
import os
import re
import smtplib
import ssl
import uuid
from email.message import EmailMessage
from pathlib import Path

log = logging.getLogger(__name__)

SEVERITY = {  # band -> (label, colour)
    "likely_fraud": ("Likely fraud", "#ef4444"),
    "high_risk": ("High risk", "#f97316"),
    "suspicious": ("Suspicious", "#eab308"),
    "safe": ("Looks safe", "#22c55e"),
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def outbox_dir() -> Path:
    default = Path(__file__).resolve().parents[3] / "data" / "interim" / "outbox"
    return Path(os.environ.get("FRAUDSHIELD_OUTBOX", default))


def smtp_configured() -> bool:
    return bool(os.environ.get("FRAUDSHIELD_SMTP_HOST"))


def render_alert(username: str, channel: str, sender: str, links: list[dict], action: str) -> tuple[str, str]:
    """(subject, html) for a message Manee checked. `links` items: {url, band, score, reasons[]}."""
    worst = max(links, key=lambda l: l["score"])
    label, colour = SEVERITY.get(worst["band"], SEVERITY["suspicious"])
    verb = "blocked" if action == "blocked" else "flagged"
    subject = f"Manee: a link in a {channel.upper()} message was {verb} ({label})"
    rows = ""
    for l in links:
        lab, col = SEVERITY.get(l["band"], SEVERITY["suspicious"])
        why = "".join(f"<li>{esc(r)}</li>" for r in l.get("reasons", [])[:3])
        rows += (
            f'<div style="border:1px solid #27272a;border-left:4px solid {col};border-radius:8px;padding:12px;margin:10px 0">'
            f'<div style="font-family:monospace;color:#fafafa;word-break:break-all">{esc(l["url"])}</div>'
            f'<div style="color:{col};font-weight:600;margin-top:6px">{esc(lab)} &middot; score {int(l["score"])}/100</div>'
            f'<ul style="color:#a1a1aa;margin:6px 0 0 18px;padding:0">{why}</ul></div>'
        )
    body = (
        '<div style="background:#09090b;padding:24px;font-family:Arial,sans-serif">'
        '<div style="max-width:560px;margin:auto;background:#18181b;border-radius:12px;padding:24px;color:#e4e4e7">'
        f'<div style="font-size:12px;letter-spacing:.08em;color:#71717a">MANEE · منيع</div>'
        f'<h2 style="margin:8px 0;color:{colour}">A link was {esc(verb)}</h2>'
        f'<p>Hi {esc(username)}, we checked a {esc(channel)} message from <b>{esc(sender)}</b> and found '
        f'{"a dangerous link" if len(links) == 1 else "dangerous links"}. <b>Do not open it</b> and do not share any codes or card details.</p>'
        f"{rows}"
        '<p style="color:#71717a;font-size:12px;margin-top:18px">You get this email because this number is on your Manee '
        'watch list. You can change alerts in Settings.</p></div></div>'
    )
    return subject, body


def send(to: str, subject: str, html_body: str) -> bool:
    """True if the email was handed to SMTP or written to the outbox."""
    try:
        sender = os.environ.get("FRAUDSHIELD_MAIL_FROM", "Manee <alerts@manee.local>")
        if not smtp_configured():
            d = outbox_dir()
            d.mkdir(parents=True, exist_ok=True)
            safe_to = re.sub(r"[^A-Za-z0-9@._-]", "_", to)
            (d / f"{uuid.uuid4().hex[:10]}_{safe_to}.html").write_text(
                f"<!-- To: {esc(to)} | Subject: {esc(subject)} -->\n{html_body}", encoding="utf-8")
            return True
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = sender, to, subject
        msg.set_content("Open this email in an HTML-capable client to see the Manee alert.")
        msg.add_alternative(html_body, subtype="html")
        host, port = os.environ["FRAUDSHIELD_SMTP_HOST"], int(os.environ.get("FRAUDSHIELD_SMTP_PORT", "587"))
        user, password = os.environ.get("FRAUDSHIELD_SMTP_USER"), os.environ.get("FRAUDSHIELD_SMTP_PASSWORD")
        ctx = ssl.create_default_context()
        if os.environ.get("FRAUDSHIELD_SMTP_SSL") == "1":
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as s:
                if user and password:
                    s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as s:
                s.starttls(context=ctx)
                if user and password:
                    s.login(user, password)
                s.send_message(msg)
        return True
    except Exception:  # never let mail break the caller
        log.exception("could not send email")
        return False
