"""Validate a checkout against current catalog facts and create one order."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog.repository import CatalogReader, catalog
from app.domain.models import CartLine, DeliveryAddress, Order, OrderItemSnapshot
from app.domain.money import add_bani, multiply_bani
from app.persistence.database import get_session_factory
from app.persistence.order_repository import (
    OrderSnapshot,
    create_order,
    get_order_by_confirmation,
)


class CheckoutLine(CartLine):
    """Untrusted browser input, deliberately limited to product ID and count."""

    model_config = ConfigDict(extra="forbid")
    quantity: int = Field(ge=1, le=99, strict=True)


class CreateOrderPayload(BaseModel):
    """Allowed order creation input; it contains no owner, price, or payment data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    items: tuple[CheckoutLine, ...] = Field(min_length=1, max_length=50)
    delivery_address: DeliveryAddress


class OrderCreationError(Exception):
    """A safe, customer-displayable checkout error."""

    def __init__(self, message: str, *, status_code: int = 422, code: str = "invalid_order") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


_ORDER_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ORDER_NUMBER_ATTEMPTS = 5


def _new_order_number(created_at: datetime) -> str:
    """Generate the documented date plus eight cryptographically random symbols."""
    suffix = "".join(secrets.choice(_ORDER_ALPHABET) for _ in range(8))
    return f"NX-{created_at:%Y%m%d}-{suffix}"


def _is_order_number_collision(error: IntegrityError) -> bool:
    """Recognize only the order-number uniqueness constraint across SQLite/Postgres."""
    detail = str(getattr(error, "orig", error)).casefold()
    return "uq_orders_order_number" in detail or "orders.order_number" in detail


def _resolve_snapshot(
    payload: CreateOrderPayload,
    *,
    repository: CatalogReader,
) -> OrderSnapshot:
    """Resolve current catalog truth and calculate all money on the server."""
    seen: set[object] = set()
    item_snapshots: list[OrderItemSnapshot] = []

    for line in payload.items:
        if line.product_id in seen:
            raise OrderCreationError("Coșul conține același produs de mai multe ori.")
        seen.add(line.product_id)

        product = repository.get_product_by_id(line.product_id)
        if product is None:
            raise OrderCreationError(
                "Un produs din coș nu mai este disponibil. Revizuiește coșul înainte de confirmare.",
                status_code=409,
                code="product_unavailable",
            )
        if line.quantity > product.stock_quantity:
            raise OrderCreationError(
                f"Stocul pentru „{product.name}” s-a schimbat. Cantitatea maximă disponibilă este {product.stock_quantity}.",
                status_code=409,
                code="stock_changed",
            )

        try:
            line_total = multiply_bani(product.price_bani, line.quantity)
            item_snapshots.append(
                OrderItemSnapshot(
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    image_url=product.image_url,
                    unit_price_bani=product.price_bani,
                    quantity=line.quantity,
                    line_total_bani=line_total,
                )
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise OrderCreationError("Datele produsului nu pot fi folosite pentru această comandă.") from exc

    subtotal = add_bani(*(item.line_total_bani for item in item_snapshots))
    created_at = datetime.now(UTC)
    return OrderSnapshot(
        id=uuid4(),
        order_number=_new_order_number(created_at),
        created_at=created_at,
        delivery_address=payload.delivery_address,
        items=tuple(item_snapshots),
        subtotal_bani=subtotal,
        shipping_bani=0,
        total_bani=add_bani(subtotal, 0),
    )


def create_customer_order(
    payload: CreateOrderPayload,
    *,
    authenticated_owner_id: str,
    confirmation_key: str,
    repository: CatalogReader = catalog,
    session_factory: Callable[[], Session] | None = None,
) -> Order:
    """Create and commit a single owner-scoped order from current server facts.

    The owner ID must come from ``get_current_user``. A new persistence session
    is opened because authentication dependencies may already have an active
    read transaction on their own request session. Repeated DB uniqueness
    collisions receive a new secure order number; all other integrity failures
    propagate so the API reports a recoverable failure and the cart is retained.
    """
    factory = session_factory or get_session_factory()
    lookup_session = factory()
    try:
        prior = get_order_by_confirmation(
            lookup_session,
            authenticated_owner_id=authenticated_owner_id,
            confirmation_key=confirmation_key,
        )
        if prior is not None:
            return prior
    finally:
        lookup_session.close()
    snapshot = _resolve_snapshot(payload, repository=repository)

    for attempt in range(_ORDER_NUMBER_ATTEMPTS):
        session = factory()
        try:
            try:
                return create_order(
                    session,
                    authenticated_owner_id=authenticated_owner_id,
                    snapshot=snapshot,
                    confirmation_key=confirmation_key,
                )
            except IntegrityError as exc:
                session.rollback()
                detail = str(getattr(exc, "orig", exc)).casefold()
                if "uq_order_confirmation_owner_key" in detail or "order_confirmations.user_id, order_confirmations.confirmation_key" in detail:
                    prior = get_order_by_confirmation(
                        session,
                        authenticated_owner_id=authenticated_owner_id,
                        confirmation_key=confirmation_key,
                    )
                    if prior is not None:
                        return prior
                if not _is_order_number_collision(exc) or attempt == _ORDER_NUMBER_ATTEMPTS - 1:
                    raise
                snapshot = snapshot.model_copy(update={"order_number": _new_order_number(snapshot.created_at)})
        finally:
            session.close()

    raise RuntimeError("Order number retry loop exited unexpectedly")
