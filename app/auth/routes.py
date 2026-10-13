"""Email/password authentication routes with opaque server-side sessions."""

from __future__ import annotations

import re
import secrets
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.auth.google import get_google_client
from app.auth.sessions import create_session, revoke_session
from app.core.config import get_settings
from app.domain.models import CustomerProfile
from app.persistence.models import OAuthIdentity, PasswordCredential, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
password_hasher = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = password_hasher.hash("nexo-market-dummy-password-for-timing")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegisterPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
    password_confirmation: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 254 or not EMAIL_RE.fullmatch(normalized):
            raise ValueError("email")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or len(value) > 128:
            raise ValueError("password")
        if len(value.encode("utf-8")) > 512:
            raise ValueError("password")
        return value


class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 254 or not EMAIL_RE.fullmatch(normalized):
            raise ValueError("email")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value or len(value.encode("utf-8")) > 512:
            raise ValueError("password")
        return value


def _profile(user: User) -> CustomerProfile:
    return CustomerProfile(id=user.id, email=user.email, display_name=user.display_name)


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def _json_payload(request: Request, schema: type[BaseModel]) -> BaseModel | JSONResponse:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        return _error(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Tipul cererii nu este acceptat.")
    try:
        raw: Any = await request.json()
    except (ValueError, UnicodeDecodeError):
        return _error(status.HTTP_400_BAD_REQUEST, "Cererea nu conține date JSON valide.")
    if not isinstance(raw, dict):
        return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Verifică datele introduse.")
    try:
        return schema.model_validate(raw)
    except ValidationError:
        return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Verifică adresa de e-mail și parola.")


def _require_same_origin(request: Request) -> None:
    """Reject cross-site auth mutations; SameSite cookies alone do not stop login CSRF."""
    settings = get_settings()
    supplied_origin = request.headers.get("origin")
    if supplied_origin is None:
        referer = request.headers.get("referer")
        supplied_origin = f"{urlsplit(referer).scheme}://{urlsplit(referer).netloc}" if referer else None
    if supplied_origin != settings.app_base_url:
        raise HTTPException(status_code=403, detail="Cererea nu a putut fi verificată.")
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        raise HTTPException(status_code=403, detail="Cererea nu a putut fi verificată.")


def _display_name(email: str) -> str:
    local_part = email.partition("@")[0]
    readable = re.sub(r"[^\w\s'-]+", " ", local_part, flags=re.UNICODE)
    readable = re.sub(r"[._+-]+", " ", readable).strip()
    readable = re.sub(r"\s+", " ", readable)
    return (readable[:120].title() or "Client Nexo")


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


_GOOGLE_RETURN_PATHS = {
    "/", "/account", "/account/orders", "/cart",
    "/checkout/details", "/checkout/review", "/search",
}


def _safe_google_return_to(value: str | None) -> str:
    """Allow only a same-origin storefront path, never an arbitrary redirect."""
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return "/account"
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        return "/account"
    path = parts.path
    allowed = (
        path in _GOOGLE_RETURN_PATHS
        or re.fullmatch(r"/account/orders/[A-Za-z0-9-]+", path) is not None
        or re.fullmatch(r"/category/[a-z0-9-]+", path) is not None
        or re.fullmatch(r"/product/[a-z0-9-]+", path) is not None
        or re.fullmatch(r"/checkout/confirmation/[A-Za-z0-9-]+", path) is not None
    )
    return path if allowed else "/account"


def _google_error_redirect(request: Request, code: str) -> RedirectResponse:
    request.session.pop("google_return_to", None)
    return RedirectResponse(f"/login?google_error={code}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/google/availability")
def google_availability() -> dict[str, bool]:
    """Expose only whether the Google provider is configured."""
    return {"available": get_google_client() is not None}


@router.get("/google")
async def google_start(
    request: Request,
    return_to: str | None = Query(default=None, max_length=512),
) -> Response:
    """Begin an OIDC authorization-code flow with state and nonce protection."""
    google = get_google_client()
    if google is None:
        return _google_error_redirect(request, "unavailable")
    request.session["google_return_to"] = _safe_google_return_to(return_to)
    nonce = secrets.token_urlsafe(32)
    try:
        return await google.authorize_redirect(
            request,
            redirect_uri=get_settings().google_redirect_uri,
            nonce=nonce,
        )
    except Exception:
        request.session.pop("google_return_to", None)
        return _google_error_redirect(request, "unavailable")


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)) -> Response:
    """Verify Google's OIDC identity, create/link safely, then issue a local session."""
    google = get_google_client()
    if google is None:
        return _google_error_redirect(request, "unavailable")
    if request.query_params.get("error") == "access_denied":
        return _google_error_redirect(request, "denied")
    return_to = _safe_google_return_to(request.session.get("google_return_to"))
    try:
        token = await google.authorize_access_token(request)
        claims = token.get("userinfo")
        # Authlib parses and verifies the ID token (including the nonce bound to
        # its OAuth state) while exchanging the code for an OIDC token response.
        if claims is None or not hasattr(claims, "get"):
            return _google_error_redirect(request, "invalid_identity")
        subject = claims.get("sub")
        email = claims.get("email")
        email_verified = claims.get("email_verified") is True
        if not isinstance(subject, str) or not subject.strip() or not isinstance(email, str):
            return _google_error_redirect(request, "invalid_identity")
        normalized_email = email.strip().lower()
        if not email_verified or len(normalized_email) > 254 or not EMAIL_RE.fullmatch(normalized_email):
            return _google_error_redirect(request, "unverified_email")

        identity = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == "google",
                OAuthIdentity.provider_subject == subject,
            )
        )
        if identity is not None:
            user = db.get(User, identity.user_id)
            if user is None or not user.is_active:
                return _google_error_redirect(request, "account_unavailable")
        else:
            # Never silently link an external identity to a password account by email.
            if db.scalar(select(User.id).where(User.email == normalized_email)) is not None:
                return _google_error_redirect(request, "account_exists")
            name = claims.get("name")
            display_name = name.strip()[:120] if isinstance(name, str) and name.strip() else _display_name(normalized_email)
            user = User(email=normalized_email, display_name=display_name)
            user.oauth_identities.append(
                OAuthIdentity(
                    provider="google",
                    provider_subject=subject,
                    provider_email=normalized_email,
                )
            )
            db.add(user)
            db.flush()

        raw_session, _record = create_session(
            db, user.id, max_age_seconds=get_settings().session_max_age_seconds
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        return _google_error_redirect(request, "account_exists")
    except Exception:
        db.rollback()
        return _google_error_redirect(request, "failed")

    request.session.pop("google_return_to", None)
    response = RedirectResponse(return_to, status_code=status.HTTP_303_SEE_OTHER)
    _set_session_cookie(response, raw_session)
    return response


@router.post("/register", response_model=CustomerProfile, status_code=status.HTTP_201_CREATED)
async def register(request: Request, db: Session = Depends(get_db)) -> CustomerProfile | JSONResponse:
    _require_same_origin(request)
    payload = await _json_payload(request, RegisterPayload)
    if isinstance(payload, JSONResponse):
        return payload
    assert isinstance(payload, RegisterPayload)
    if payload.password != payload.password_confirmation:
        return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Parolele nu coincid.")

    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        return _error(status.HTTP_409_CONFLICT, "Există deja un cont cu această adresă de e-mail.")

    user = User(email=payload.email, display_name=_display_name(payload.email))
    credential = PasswordCredential(password_hash=password_hasher.hash(payload.password))
    user.password_credential = credential
    try:
        db.add(user)
        db.flush()
        token, _session = create_session(
            db, user.id, max_age_seconds=get_settings().session_max_age_seconds
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        return _error(status.HTTP_409_CONFLICT, "Există deja un cont cu această adresă de e-mail.")
    except Exception:
        db.rollback()
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Contul nu a putut fi creat acum.")

    response = JSONResponse(status_code=status.HTTP_201_CREATED, content=_profile(user).model_dump(mode="json"))
    _set_session_cookie(response, token)
    return response


@router.post("/login", response_model=CustomerProfile)
async def login(request: Request, db: Session = Depends(get_db)) -> CustomerProfile | JSONResponse:
    _require_same_origin(request)
    payload = await _json_payload(request, LoginPayload)
    if isinstance(payload, JSONResponse):
        return payload
    assert isinstance(payload, LoginPayload)

    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    credential = user.password_credential if user is not None else None
    valid = password_hasher.verify(payload.password, _DUMMY_PASSWORD_HASH) if credential is None else False
    if credential is not None:
        try:
            valid = password_hasher.verify(payload.password, credential.password_hash)
        except (ValueError, TypeError):
            valid = False
    if not valid or user is None:
        return _error(status.HTTP_401_UNAUTHORIZED, "Adresa de e-mail sau parola este incorectă.")

    try:
        token, _session = create_session(
            db, user.id, max_age_seconds=get_settings().session_max_age_seconds
        )
        db.commit()
    except Exception:
        db.rollback()
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Autentificarea nu este disponibilă acum.")

    response = JSONResponse(status_code=status.HTTP_200_OK, content=_profile(user).model_dump(mode="json"))
    _set_session_cookie(response, token)
    return response


@router.get("/me", response_model=CustomerProfile)
def get_me(current_user: User = Depends(get_current_user)) -> CustomerProfile:
    """Return safe customer identity fields for the current cookie session."""
    return _profile(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    """Revoke the current opaque session and expire its HttpOnly cookie."""
    _require_same_origin(request)
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    try:
        revoke_session(db, token)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nu te-ai putut deconecta acum. Încearcă din nou.",
        )

    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
