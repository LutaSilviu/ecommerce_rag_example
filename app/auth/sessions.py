"""Opaque, revocable browser sessions backed by hashed cookie tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import SessionRecord


def _token_hash(token: str) -> str:
    """Hash an opaque cookie token before it is ever persisted or queried."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    db: Session,
    user_id: str,
    *,
    max_age_seconds: int,
    now: datetime | None = None,
) -> tuple[str, SessionRecord]:
    """Create a session and return its raw token once for setting an HttpOnly cookie.

    The caller owns the transaction and must commit before sending the cookie.
    Only the SHA-256 digest is stored in the session row.
    """
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")

    current_time = now or datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    record = SessionRecord(
        user_id=user_id,
        token_hash=_token_hash(token),
        created_at=current_time,
        last_seen_at=current_time,
        expires_at=current_time + timedelta(seconds=max_age_seconds),
    )
    db.add(record)
    db.flush()
    return token, record


def lookup_session(
    db: Session,
    token: str | None,
    *,
    now: datetime | None = None,
) -> SessionRecord | None:
    """Return a live session for a presented token; invalid tokens return ``None``."""
    if not token:
        return None

    record = db.scalar(select(SessionRecord).where(SessionRecord.token_hash == _token_hash(token)))
    if record is None or record.revoked_at is not None:
        return None

    current_time = now or datetime.now(timezone.utc)
    expires_at = record.expires_at
    # SQLite can return a naive datetime for a timezone-aware column.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= current_time:
        return None
    return record


def revoke_session(
    db: Session,
    token: str | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Revoke a live session by token and report whether a row was changed."""
    record = lookup_session(db, token, now=now)
    if record is None:
        return False
    record.revoked_at = now or datetime.now(timezone.utc)
    db.flush()
    return True
