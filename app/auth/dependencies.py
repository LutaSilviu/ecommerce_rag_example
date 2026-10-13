"""Request dependencies for resolving a signed-in customer from a cookie."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.persistence.database import get_session_factory
from app.persistence.models import User
from app.auth.sessions import lookup_session


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Require a valid, unexpired server session and an active local account."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    session_record = lookup_session(db, token)
    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )

    user = db.get(User, session_record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"},
        )
    return user
