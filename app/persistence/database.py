"""SQLAlchemy engine and session-factory configuration.

This module provides database access primitives only. Request-scoped session
lifecycle and authentication behavior belong to their respective layers.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def _prepare_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return
    if url.database == ":memory:" or url.database.startswith("file:"):
        return

    database_path = Path(url.database)
    if database_path.parent != Path("."):
        database_path.parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(settings: Settings | None = None) -> Engine:
    """Build an engine using the configured URL and SQLite-safe options."""
    configuration = settings or get_settings()
    database_url = configuration.database_url
    options: dict[str, object] = {"pool_pre_ping": True}

    if make_url(database_url).get_backend_name() == "sqlite":
        _prepare_sqlite_parent(database_url)
        options["connect_args"] = {"check_same_thread": False}
        engine = create_engine(database_url, **options)

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(database_url, **options)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide engine using current validated settings."""
    return create_database_engine()


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Return the shared factory; callers own opening/closing each Session."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)

