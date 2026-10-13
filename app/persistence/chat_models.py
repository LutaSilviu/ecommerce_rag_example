"""Persistent cache for semantic vectors derived from catalog product text."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class CatalogEmbeddingRecord(Base):
    __tablename__ = "catalog_product_embeddings"

    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("catalog_products.id", ondelete="CASCADE"), primary_key=True
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    vector_json: Mapped[str] = mapped_column(Text, nullable=False)
