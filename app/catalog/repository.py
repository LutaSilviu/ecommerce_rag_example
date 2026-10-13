"""Typed, read-only catalog access over memory and persistent SQL adapters.

Application and API code should depend on :class:`CatalogReader` rather than
importing seed constants. A future database adapter can implement the same
interface without changing catalog consumers.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import unicodedata
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from pydantic import ConfigDict

from app.catalog.seed import CATEGORY_SEEDS, PRODUCT_SEEDS, PRODUCT_SLUGS
from app.domain.models import Category, Product
from app.persistence.catalog_models import CatalogCategoryRecord, CatalogProductRecord
from app.persistence.database import get_session_factory
from sqlalchemy import select


class CatalogProduct(Product):
    """A product read model that includes its stable storefront slug."""

    slug: str

    model_config = ConfigDict(extra="forbid", frozen=True)


class CatalogCategory(Category):
    """Immutable category read model returned by the catalog boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class CatalogReader(Protocol):
    """Read-only interface consumed by routes and other application services."""

    def list_products(
        self,
        *,
        category_slug: str | None = None,
        query: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[CatalogProduct, ...]:
        """Return products, optionally filtered by category and text query."""

    def get_product_by_id(self, product_id: UUID) -> CatalogProduct | None:
        """Return one active product by stable UUID, if present."""

    def get_product_by_slug(self, slug: str) -> CatalogProduct | None:
        """Return one active product by stable storefront slug, if present."""

    def search_products(
        self,
        query: str,
        *,
        category_slug: str | None = None,
    ) -> tuple[CatalogProduct, ...]:
        """Search product name, description, SKU, and category name."""

    def list_categories(self, *, include_inactive: bool = False) -> tuple[CatalogCategory, ...]:
        """Return categories in their declared display order."""

    def get_category_by_id(self, category_id: UUID) -> CatalogCategory | None:
        """Return a category by stable UUID, if present and active."""

    def get_category_by_slug(self, slug: str) -> CatalogCategory | None:
        """Return a category by stable slug, if present and active."""


class InMemoryCatalogRepository:
    """Seed-backed catalog adapter with deterministic, read-only operations."""

    def __init__(
        self,
        products: Iterable[Product] = PRODUCT_SEEDS,
        categories: Iterable[Category] = CATEGORY_SEEDS,
        product_slugs: Mapping[UUID, str] = PRODUCT_SLUGS,
    ) -> None:
        category_rows = tuple(
            CatalogCategory.model_validate(category.model_dump()) for category in categories
        )
        category_by_id = {category.id: category for category in category_rows}
        category_by_slug = {category.slug: category for category in category_rows}
        if len(category_by_id) != len(category_rows) or len(category_by_slug) != len(category_rows):
            raise ValueError("Catalog categories must have unique IDs and slugs")

        slugs = dict(product_slugs)
        product_rows: list[CatalogProduct] = []
        for product in products:
            slug = slugs.get(product.id)
            if not slug:
                raise ValueError(f"Missing catalog slug for product {product.id}")
            if product.category_id not in category_by_id:
                raise ValueError(f"Unknown category {product.category_id} for product {product.id}")
            product_rows.append(
                CatalogProduct.model_validate({**product.model_dump(), "slug": slug})
            )

        product_by_id = {product.id: product for product in product_rows}
        product_by_slug = {product.slug: product for product in product_rows}
        if len(product_by_id) != len(product_rows) or len(product_by_slug) != len(product_rows):
            raise ValueError("Catalog products must have unique IDs and slugs")

        self._categories = tuple(sorted(category_rows, key=lambda row: (row.sort_order, row.slug)))
        self._category_by_id = MappingProxyType(category_by_id)
        self._category_by_slug = MappingProxyType(category_by_slug)
        self._products = tuple(product_rows)
        self._product_by_id = MappingProxyType(product_by_id)
        self._product_by_slug = MappingProxyType(product_by_slug)

    def list_products(
        self,
        *,
        category_slug: str | None = None,
        query: str | None = None,
        include_inactive: bool = False,
    ) -> tuple[CatalogProduct, ...]:
        category = self._category_by_slug.get(category_slug) if category_slug else None
        if category_slug is not None and category is None:
            return ()
        if category is not None and not include_inactive and not category.is_active:
            return ()
        return tuple(
            product
            for product in self._products
            if (include_inactive or product.is_active)
            and (category is None or product.category_id == category.id)
            and self._matches_query(product, query)
        )

    def get_product_by_id(self, product_id: UUID) -> CatalogProduct | None:
        product = self._product_by_id.get(product_id)
        return product if product is not None and product.is_active else None

    def get_product_by_slug(self, slug: str) -> CatalogProduct | None:
        product = self._product_by_slug.get(slug)
        return product if product is not None and product.is_active else None

    def search_products(
        self,
        query: str,
        *,
        category_slug: str | None = None,
    ) -> tuple[CatalogProduct, ...]:
        return self.list_products(category_slug=category_slug, query=query)

    def list_categories(self, *, include_inactive: bool = False) -> tuple[CatalogCategory, ...]:
        return tuple(
            category for category in self._categories if include_inactive or category.is_active
        )

    def get_category_by_id(self, category_id: UUID) -> CatalogCategory | None:
        category = self._category_by_id.get(category_id)
        return category if category is not None and category.is_active else None

    def get_category_by_slug(self, slug: str) -> CatalogCategory | None:
        category = self._category_by_slug.get(slug)
        return category if category is not None and category.is_active else None

    def _matches_query(self, product: CatalogProduct, query: str | None) -> bool:
        if query is None or not query.strip():
            return True
        category = self._category_by_id[product.category_id]
        searchable = _normalize_search_text(
            " ".join((product.name, product.description, product.sku, category.name))
        )
        return all(term in searchable for term in _normalize_search_text(query).split())


class DatabaseCatalogRepository:
    """SQL-backed catalog reader that preserves the public read contract."""

    def _memory_view(self) -> InMemoryCatalogRepository:
        session = get_session_factory()()
        try:
            categories = session.scalars(select(CatalogCategoryRecord)).all()
            rows = session.scalars(select(CatalogProductRecord)).all()
            category_models = tuple(
                Category(
                    id=UUID(row.id), slug=row.slug, name=row.name,
                    description=row.description, sort_order=row.sort_order,
                    is_active=row.is_active,
                )
                for row in categories
            )
            products = tuple(
                Product(
                    id=UUID(row.id), sku=row.sku, category_id=UUID(row.category_id),
                    name=row.name, description=row.description, price_bani=row.price_bani,
                    image_url=row.image_url, stock_quantity=row.stock_quantity,
                    is_active=row.is_active,
                )
                for row in rows
            )
            slugs = {UUID(row.id): row.slug for row in rows}
            return InMemoryCatalogRepository(products, category_models, slugs)
        finally:
            session.close()

    def list_products(self, *, category_slug: str | None = None, query: str | None = None,
                      include_inactive: bool = False) -> tuple[CatalogProduct, ...]:
        return self._memory_view().list_products(
            category_slug=category_slug, query=query, include_inactive=include_inactive
        )

    def get_product_by_id(self, product_id: UUID) -> CatalogProduct | None:
        return self._memory_view().get_product_by_id(product_id)

    def get_product_by_slug(self, slug: str) -> CatalogProduct | None:
        return self._memory_view().get_product_by_slug(slug)

    def search_products(self, query: str, *, category_slug: str | None = None) -> tuple[CatalogProduct, ...]:
        return self._memory_view().search_products(query, category_slug=category_slug)

    def list_categories(self, *, include_inactive: bool = False) -> tuple[CatalogCategory, ...]:
        return self._memory_view().list_categories(include_inactive=include_inactive)

    def get_category_by_id(self, category_id: UUID) -> CatalogCategory | None:
        return self._memory_view().get_category_by_id(category_id)

    def get_category_by_slug(self, slug: str) -> CatalogCategory | None:
        return self._memory_view().get_category_by_slug(slug)


def _normalize_search_text(value: str) -> str:
    """Casefold and remove combining marks for accent-insensitive matching.

    Romanian text can use both comma-below and legacy cedilla characters for
    ș/ț. NFD separates either spelling into a base letter plus a mark, so an
    unaccented query such as ``ingrijire`` matches ``Îngrijire`` consistently.
    """

    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


catalog: CatalogReader = DatabaseCatalogRepository()


__all__ = [
    "CatalogCategory",
    "CatalogProduct",
    "CatalogReader",
    "DatabaseCatalogRepository",
    "InMemoryCatalogRepository",
    "catalog",
]
