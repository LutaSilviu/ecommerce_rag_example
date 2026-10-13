"""Read-only catalog API endpoints used by the storefront shell."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.catalog.repository import CatalogCategory, CatalogProduct, catalog

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CatalogCategory])
def list_categories() -> list[CatalogCategory]:
    """Return active categories in the canonical storefront display order."""

    return list(catalog.list_categories())


@router.get("/products", response_model=list[CatalogProduct])
def list_products(
    category_slug: str | None = Query(default=None, min_length=1, max_length=80),
    q: str | None = Query(default=None, max_length=200),
) -> list[CatalogProduct]:
    """Return active products, optionally filtered for reusable catalog views.

    Unknown category slugs produce an empty list, matching the repository
    contract and allowing category pages to render their own empty state.
    """

    return list(catalog.list_products(category_slug=category_slug, query=q))


@router.get("/products/{product_slug}", response_model=CatalogProduct)
def get_product(product_slug: str) -> CatalogProduct:
    """Return one active product by its stable URL slug or UUID."""

    product = catalog.get_product_by_slug(product_slug)
    if product is None:
        try:
            product = catalog.get_product_by_id(UUID(product_slug))
        except ValueError:
            product = None
    if product is None:
        raise HTTPException(status_code=404, detail="Produsul nu a fost găsit.")
    return product


@router.get("/products/by-id/{product_id}", response_model=CatalogProduct)
def get_product_by_id(product_id: UUID) -> CatalogProduct:
    """Resolve a product by its stable UUID for clients holding cart IDs."""

    product = catalog.get_product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produsul nu a fost găsit.")
    return product
