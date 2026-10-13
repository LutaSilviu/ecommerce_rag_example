"""Relational catalog records; public contracts stay in app.domain.models."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.base import Base


class CatalogCategoryRecord(Base):
    __tablename__ = "catalog_categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_catalog_categories_slug"),
        CheckConstraint("sort_order >= 0", name="ck_catalog_categories_sort_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    products: Mapped[list[CatalogProductRecord]] = relationship(back_populates="category")


class CatalogProductRecord(Base):
    __tablename__ = "catalog_products"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_catalog_products_sku"),
        UniqueConstraint("slug", name="uq_catalog_products_slug"),
        CheckConstraint("price_bani >= 0", name="ck_catalog_products_price"),
        CheckConstraint("stock_quantity >= 0", name="ck_catalog_products_stock"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("catalog_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    price_bani: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped[CatalogCategoryRecord] = relationship(back_populates="products")
