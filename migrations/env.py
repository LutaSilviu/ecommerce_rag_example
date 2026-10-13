"""Alembic environment using the application's configured SQLAlchemy engine."""

from alembic import context

from app.core.config import get_settings
from app.persistence.base import Base
from app.persistence.catalog_models import CatalogCategoryRecord, CatalogProductRecord
from app.persistence.chat_models import CatalogEmbeddingRecord

config = context.config
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from app.persistence.database import get_engine

    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
