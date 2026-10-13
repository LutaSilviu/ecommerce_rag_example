"""Validated server-side settings for the local Nexo Market application.

Configuration is read on demand so importing the FastAPI app does not require a
developer's local ``.env`` file. This module deliberately does not initialize an
OAuth client, database connection, or session behavior.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit


class SettingsError(ValueError):
    """Raised when an explicitly supplied setting is malformed or inconsistent."""


def _boolean(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be one of true/false, yes/no, on/off, or 1/0")


def _origin(name: str, value: str) -> str:
    parts = urlsplit(value.strip())
    if (
        parts.scheme not in {"http", "https"}
        or not parts.netloc
        or parts.username is not None
        or parts.password is not None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
    ):
        raise SettingsError(f"{name} must be an absolute HTTP(S) origin without a path")
    return f"{parts.scheme}://{parts.netloc}"


def _callback(name: str, value: str, expected_origin: str) -> str:
    parts = urlsplit(value.strip())
    if (
        parts.scheme not in {"http", "https"}
        or not parts.netloc
        or parts.username is not None
        or parts.password is not None
        or parts.path != "/api/v1/auth/google/callback"
        or parts.query
        or parts.fragment
    ):
        raise SettingsError(
            f"{name} must end with /api/v1/auth/google/callback and contain no query or fragment"
        )
    callback_origin = f"{parts.scheme}://{parts.netloc}"
    if callback_origin != expected_origin:
        raise SettingsError(f"{name} must use the same origin as APP_BASE_URL")
    return value.strip()


def _is_placeholder(value: str) -> bool:
    return not value.strip() or "replace-with" in value.strip().lower()


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed local/server configuration, with secrets kept server-side."""

    database_url: str
    session_secret: str
    session_cookie_name: str
    session_max_age_seconds: int
    session_cookie_secure: bool
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    app_base_url: str
    google_oauth_enabled: bool
    openai_model: str = "gpt-6-luna"
    openai_embedding_model: str = "text-embedding-3-small"

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None) -> "Settings":
        """Parse and validate settings, defaulting to the documented local URLs."""
        source = os.environ if environ is None else environ

        def get(name: str, default: str) -> str:
            return source.get(name, default).strip()

        # Render provides the canonical HTTPS URL at runtime. Keeping this as a
        # fallback lets OAuth work after registering the generated callback URL.
        base_url = _origin(
            "APP_BASE_URL",
            get("APP_BASE_URL", get("RENDER_EXTERNAL_URL", "http://localhost:8000")),
        )
        callback = _callback(
            "GOOGLE_REDIRECT_URI",
            get(
                "GOOGLE_REDIRECT_URI",
                f"{base_url}/api/v1/auth/google/callback",
            ),
            base_url,
        )

        try:
            max_age = int(get("SESSION_MAX_AGE_SECONDS", "604800"))
        except ValueError as exc:
            raise SettingsError("SESSION_MAX_AGE_SECONDS must be a positive integer") from exc
        if max_age <= 0:
            raise SettingsError("SESSION_MAX_AGE_SECONDS must be a positive integer")

        client_id = get("GOOGLE_CLIENT_ID", "replace-with-google-oauth-client-id")
        client_secret = get(
            "GOOGLE_CLIENT_SECRET", "replace-with-google-oauth-client-secret"
        )
        id_is_placeholder = _is_placeholder(client_id)
        secret_is_placeholder = _is_placeholder(client_secret)
        if id_is_placeholder != secret_is_placeholder:
            raise SettingsError(
                "Set both GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, or leave both as placeholders"
            )
        google_enabled = not id_is_placeholder and not secret_is_placeholder

        secret = get("SESSION_SECRET", "local-development-only-change-me")
        secure_default = "true" if base_url.startswith("https://") else "false"
        cookie_secure = _boolean(
            "SESSION_COOKIE_SECURE", get("SESSION_COOKIE_SECURE", secure_default)
        )
        if base_url.startswith("https://") and not cookie_secure:
            raise SettingsError("SESSION_COOKIE_SECURE must be true when APP_BASE_URL uses HTTPS")

        return cls(
            database_url=get("DATABASE_URL", "sqlite:///./data/nexo-market.db"),
            session_secret=secret,
            session_cookie_name=get("SESSION_COOKIE_NAME", "nexo_session"),
            session_max_age_seconds=max_age,
            session_cookie_secure=cookie_secure,
            google_client_id=client_id,
            google_client_secret=client_secret,
            google_redirect_uri=callback,
            app_base_url=base_url,
            google_oauth_enabled=google_enabled,
            openai_model=get("OPENAI_MODEL", "gpt-6-luna"),
            openai_embedding_model=get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-cached settings; clear this cache after changing env vars."""
    return Settings.from_environment()
