"""Lazy Authlib client setup for Google OpenID Connect.

The public storefront can import this module without configured Google OAuth
credentials. Routes that need Google sign-in should call
``get_google_client`` and handle ``None`` as an unavailable provider.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from authlib.integrations.starlette_client import OAuth

from app.core.config import Settings, get_settings

GOOGLE_OIDC_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_OIDC_SCOPES = "openid email profile"


@lru_cache(maxsize=4)
def _registered_google_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> Any:
    """Build and cache a configured Google client for this process."""
    registry = OAuth()
    registry.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        server_metadata_url=GOOGLE_OIDC_METADATA_URL,
        client_kwargs={"scope": GOOGLE_OIDC_SCOPES},
    )
    return registry.google


def get_google_client(settings: Settings | None = None) -> Any | None:
    """Return the Authlib Google OIDC client when credentials are configured.

    ``Settings.google_oauth_enabled`` is false for the documented placeholder
    values. In that case no OAuth client is registered and callers can leave
    Google sign-in unavailable without affecting public storefront routes.
    """
    config = settings if settings is not None else get_settings()
    if not config.google_oauth_enabled:
        return None

    return _registered_google_client(
        config.google_client_id,
        config.google_client_secret,
        config.google_redirect_uri,
    )

