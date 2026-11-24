"""Passwords and session tokens using only the standard library.

Passwords: scrypt with a random salt (never stored or logged in clear).
Sessions: a signed token "user|role|expiry" (HMAC-SHA256) in an HttpOnly cookie. Stateless, so logging out removes
the cookie but a copied token stays valid until it expires (8 hours); a real deployment would add server-side revoke.
The signing secret comes from FRAUDSHIELD_SECRET, or is generated once and kept next to the database.
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

ROLES = ("user", "analyst", "admin")
STAFF_ROLES = ("analyst", "admin")
SESSION_SECONDS = 8 * 3600
COOKIE = "fs_session"


def auth_enabled() -> bool:
    """On by default. Tests and quick local demos can set FRAUDSHIELD_AUTH=0."""
    return os.environ.get("FRAUDSHIELD_AUTH", "1") != "0"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest, base64.b64decode(digest_b64))
    except (ValueError, TypeError):
        return False


def _secret() -> bytes:
    env = os.environ.get("FRAUDSHIELD_SECRET")
    if env:
        return env.encode()
    from app.repositories.scan_repo import db_path

    path = Path(db_path()).with_name("session.key")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip().encode()


def make_token(username: str, role: str, now: float | None = None) -> str:
    expiry = int((now if now is not None else time.time()) + SESSION_SECONDS)
    body = f"{username}|{role}|{expiry}"
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{body}|{sig}".encode()).decode()


def read_token(token: str, now: float | None = None) -> tuple[str, str] | None:
    """Return (username, role) for a valid, unexpired token, else None."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, role, expiry, sig = raw.rsplit("|", 3)
        body = f"{username}|{role}|{expiry}"
        good = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good) or role not in ROLES:
            return None
        if int(expiry) < (now if now is not None else time.time()):
            return None
        return username, role
    except (ValueError, UnicodeError):
        return None
