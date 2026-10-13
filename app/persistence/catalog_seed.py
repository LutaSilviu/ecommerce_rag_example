"""One-time-safe import of bundled demo records into SQL catalog tables."""

from app.catalog.seed import CATEGORY_SEEDS, PRODUCT_SEEDS, PRODUCT_SLUGS
from app.persistence.catalog_models import CatalogCategoryRecord, CatalogProductRecord
from app.persistence.database import get_session_factory


def seed_catalog_data() -> None:
    """Insert missing demo records while preserving persisted catalog edits.

    This runs at startup for an existing database that may predate the catalog
    tables. Existing rows are intentionally never overwritten: operational price,
    stock, copy, or active-state edits survive restarts. Catalog edits should be
    made through a future management path or a new explicit data migration.
    """
    session = get_session_factory()()
    try:
        for category in CATEGORY_SEEDS:
            record = session.get(CatalogCategoryRecord, str(category.id))
            if record is None:
                session.add(
                    CatalogCategoryRecord(
                        id=str(category.id), slug=category.slug, name=category.name,
                        description=category.description, sort_order=category.sort_order,
                        is_active=category.is_active,
                    )
                )

        session.flush()
        for product in PRODUCT_SEEDS:
            record = session.get(CatalogProductRecord, str(product.id))
            if record is None:
                session.add(
                    CatalogProductRecord(
                        id=str(product.id), sku=product.sku, slug=PRODUCT_SLUGS[product.id],
                        category_id=str(product.category_id), name=product.name,
                        description=product.description, price_bani=product.price_bani,
                        image_url=str(product.image_url) if product.image_url else None,
                        stock_quantity=product.stock_quantity, is_active=product.is_active,
                    )
                )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
