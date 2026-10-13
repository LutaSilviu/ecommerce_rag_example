"""Shared declarative base for SQLAlchemy persistence records."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for application-owned database records."""

