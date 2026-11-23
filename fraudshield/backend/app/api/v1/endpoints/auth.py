from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import client_key, current_user
from app.core.auth import COOKIE, SESSION_SECONDS, auth_enabled, make_token, verify_password
from app.core.rate_limit import SlidingWindowLimiter
from app.repositories import user_repo
from app.services import audit_service

router = APIRouter(prefix="/auth")
limiter = SlidingWindowLimiter(max_hits=10, window_seconds=300)  # 10 login attempts per 5 min per client

# Checked even for unknown users so timing does not reveal which usernames exist.
_DUMMY = "scrypt$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
def login(body: Login, request: Request, response: Response) -> dict:
    if not limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again in a few minutes.")
    user = user_repo.get(body.username.strip())
    ok = verify_password(body.password, user["password_hash"] if user else _DUMMY)
    if not user or not ok:
        audit_service.record(body.username.strip()[:80] or "?", "auth.login_failed", "user", body.username.strip()[:80])
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    response.set_cookie(COOKIE, make_token(user["username"], user["role"]), max_age=SESSION_SECONDS,
                        httponly=True, samesite="lax", secure=request.url.scheme == "https", path="/")
    audit_service.record(user["username"], "auth.login", "user", user["username"])
    return {"username": user["username"], "role": user["role"]}


@router.post("/logout")
def logout(response: Response, user: tuple[str, str] | None = Depends(current_user)) -> dict:
    response.delete_cookie(COOKIE, path="/")
    if user:
        audit_service.record(user[0], "auth.logout", "user", user[0])
    return {"ok": True}


@router.get("/me")
def me(user: tuple[str, str] | None = Depends(current_user)) -> dict:
    """Who is signed in. With auth switched off, everyone is an admin (a demo/test mode)."""
    if not auth_enabled():
        return {"username": "demo", "role": "admin", "auth_enabled": False}
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return {"username": user[0], "role": user[1], "auth_enabled": True}
