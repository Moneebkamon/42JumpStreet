from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.deps import client_key, current_user, require_user
import re

from app.core.auth import COOKIE, SESSION_SECONDS, auth_enabled, hash_password, make_token, verify_password
from app.core.rate_limit import SlidingWindowLimiter
from app.repositories import user_repo
from app.services import audit_service

router = APIRouter(prefix="/auth")
limiter = SlidingWindowLimiter(max_hits=10, window_seconds=300)  # 10 login attempts per 5 min per client

# Checked even for unknown users so timing does not reveal which usernames exist.
_DUMMY = "scrypt$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


register_limiter = SlidingWindowLimiter(max_hits=5, window_seconds=3600)  # 5 sign-ups per hour per client
_USERNAME = re.compile(r"^[A-Za-z0-9_.-]{3,40}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Register(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


def _start_session(response: Response, request: Request, username: str, role: str) -> None:
    response.set_cookie(COOKIE, make_token(username, role), max_age=SESSION_SECONDS,
                        httponly=True, samesite="lax", secure=request.url.scheme == "https", path="/")


@router.post("/register", status_code=201)
def register(body: Register, request: Request, response: Response) -> dict:
    """Public sign-up. Always creates a regular "user"; staff roles are only given from the command line."""
    if not register_limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many sign-ups from your connection. Try again later.")
    username, email = body.username.strip(), body.email.strip().lower()
    if not _USERNAME.match(username):
        raise HTTPException(status_code=422, detail="Username: 3-40 letters, digits, dot, dash or underscore.")
    if not _EMAIL.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if not user_repo.create(username, email, hash_password(body.password), "user"):
        raise HTTPException(status_code=409, detail="That username or email is already registered.")
    audit_service.record(username, "auth.register", "user", username)
    _start_session(response, request, username, "user")
    return {"username": username, "role": "user", "email": email}


@router.post("/password")
def change_password(body: ChangePassword, user: tuple[str, str] = Depends(require_user)) -> dict:
    row = user_repo.get(user[0])
    if not row or not verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(status_code=403, detail="Current password is wrong.")
    user_repo.set_password(user[0], hash_password(body.new_password))
    audit_service.record(user[0], "auth.password_changed", "user", user[0])
    return {"ok": True}


@router.post("/login")
def login(body: Login, request: Request, response: Response) -> dict:
    if not limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again in a few minutes.")
    user = user_repo.get(body.username.strip())
    ok = verify_password(body.password, user["password_hash"] if user else _DUMMY)
    if not user or not ok:
        audit_service.record(body.username.strip()[:80] or "?", "auth.login_failed", "user", body.username.strip()[:80])
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    _start_session(response, request, user["username"], user["role"])
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
        return {"username": "demo", "role": "admin", "email": None, "auth_enabled": False}
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    row = user_repo.get(user[0]) or {}
    return {"username": user[0], "role": user[1], "email": row.get("email"), "auth_enabled": True}
