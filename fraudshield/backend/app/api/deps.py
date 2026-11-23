"""Shared request helpers: who is calling, and what they may do.

Auth is on by default (FRAUDSHIELD_AUTH=0 turns it off for tests and quick demos). Staff log in at /auth/login and get a
signed HttpOnly cookie. Roles: "analyst" (cases, evidence, drafts, feed) and "admin" (everything an analyst can, plus the
audit log). Public routes (scanning a link, the citizen report form) need no login.
With auth off, the actor is just a label from the X-Actor header and everyone is treated as an admin.
"""
from fastapi import Depends, Header, HTTPException, Request

from app.core.auth import COOKIE, auth_enabled, read_token


def current_user(request: Request) -> tuple[str, str] | None:
    token = request.cookies.get(COOKIE)
    return read_token(token) if token else None


def require_analyst(user: tuple[str, str] | None = Depends(current_user)) -> tuple[str, str] | None:
    if not auth_enabled():
        return None
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in.")
    return user  # analyst and admin may both pass


def require_admin(user: tuple[str, str] | None = Depends(current_user)) -> tuple[str, str] | None:
    if not auth_enabled():
        return None
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in.")
    if user[1] != "admin":
        raise HTTPException(status_code=403, detail="This needs an administrator.")
    return user


def get_actor(user: tuple[str, str] | None = Depends(current_user), x_actor: str = Header(default="analyst", max_length=80)) -> str:
    if auth_enabled():
        return user[0] if user else "anonymous"  # a verified name, never the header
    return x_actor.strip() or "analyst"


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"
