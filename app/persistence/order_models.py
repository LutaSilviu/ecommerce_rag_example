"""ORM records for immutable, customer-owned prototype orders."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.base import Base


def _new_id() -> str:
    return str(uuid4())


class OrderRecord(Base):
    """Order header with flattened delivery-address and money snapshots."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_orders_order_number"),
        CheckConstraint("status = 'registered'", name="ck_orders_registered_only"),
        CheckConstraint("payment_method = 'simulated'", name="ck_orders_simulated_method"),
        CheckConstraint("payment_status = 'not_processed'", name="ck_orders_not_processed"),
        CheckConstraint("subtotal_bani >= 0", name="ck_orders_subtotal_nonnegative"),
        CheckConstraint("shipping_bani = 0", name="ck_orders_shipping_zero"),
        CheckConstraint("total_bani = subtotal_bani + shipping_bani", name="ck_orders_total"),
        Index("ix_orders_owner_created", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="registered")
    payment_method: Mapped[str] = mapped_column(String(24), nullable=False, default="simulated")
    payment_status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_processed")

    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(24), nullable=False)
    county: Mapped[str] = mapped_column(String(80), nullable=False)
    locality: Mapped[str] = mapped_column(String(100), nullable=False)
    street_address: Mapped[str] = mapped_column(String(200), nullable=False)
    building: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entrance: Mapped[str | None] = mapped_column(String(30), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    apartment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(6), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="RO")

    subtotal_bani: Mapped[int] = mapped_column(Integer, nullable=False)
    shipping_bani: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_bani: Mapped[int] = mapped_column(Integer, nullable=False)

    items: Mapped[list[OrderItemRecord]] = relationship(
        back_populates="order", cascade="all, delete-orphan", passive_deletes=True,
        order_by="OrderItemRecord.position",
    )


class OrderItemRecord(Base):
    """Append-only item facts as they were presented at order confirmation."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_order_items_position"),
        CheckConstraint("unit_price_bani >= 0", name="ck_order_items_price"),
        CheckConstraint("quantity BETWEEN 1 AND 99", name="ck_order_items_quantity"),
        CheckConstraint("line_total_bani = unit_price_bani * quantity", name="ck_order_items_line_total"),
        UniqueConstraint("order_id", "position", name="uq_order_items_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    unit_price_bani: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_bani: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[OrderRecord] = relationship(back_populates="items")


class OrderConfirmationRecord(Base):
    """Durable per-customer idempotency key bound to its committed order."""

    __tablename__ = "order_confirmations"
    __table_args__ = (
        UniqueConstraint("user_id", "confirmation_key", name="uq_order_confirmation_owner_key"),
        UniqueConstraint("order_id", name="uq_order_confirmation_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    confirmation_key: Mapped[str] = mapped_column(String(36), nullable=False)
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
