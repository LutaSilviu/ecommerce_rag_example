"""Owner-scoped persistence operations for immutable prototype orders.

Order writes accept an authenticated owner supplied by trusted server code and
a snapshot payload that intentionally has no customer/owner field. The caller
must pass a fresh SQLAlchemy Session to ``create_order`` so its transaction
commits the complete header, address, and item set together.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from pydantic import ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models import (
    DeliveryAddress,
    DomainModel,
    MockPaymentState,
    Order,
    OrderItemSnapshot,
    OrderStatus,
)
from app.persistence.order_models import OrderConfirmationRecord, OrderItemRecord, OrderRecord


_ORDER_NUMBER = re.compile(r"^NX-\d{8}-[0-9A-HJKMNP-TV-Z]{8}$")


class OrderSnapshot(DomainModel):
    """Server-prepared order facts; deliberately excludes customer ownership.

    T029 is responsible for resolving catalog products and calculating these
    values. This type validates their internal arithmetic before persistence.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    id: UUID
    order_number: str = Field(pattern=r"^NX-\d{8}-[0-9A-HJKMNP-TV-Z]{8}$")
    created_at: datetime
    delivery_address: DeliveryAddress
    items: tuple[OrderItemSnapshot, ...] = Field(min_length=1)
    subtotal_bani: int = Field(ge=0)
    shipping_bani: int = Field(default=0, ge=0)
    total_bani: int = Field(ge=0)

    def validate_contract(self) -> None:
        """Reject snapshots inconsistent with the shared cart/order contract."""
        if not _ORDER_NUMBER.fullmatch(self.order_number):
            raise ValueError("order_number does not follow the Nexo order format")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if self.shipping_bani != 0:
            raise ValueError("shipping_bani must remain zero for this prototype")
        expected_subtotal = sum(item.unit_price_bani * item.quantity for item in self.items)
        if any(item.line_total_bani != item.unit_price_bani * item.quantity for item in self.items):
            raise ValueError("each line total must equal unit price multiplied by quantity")
        if self.subtotal_bani != expected_subtotal:
            raise ValueError("subtotal_bani must equal the sum of item snapshot totals")
        if self.total_bani != self.subtotal_bani + self.shipping_bani:
            raise ValueError("total_bani must equal subtotal plus shipping")


def create_order(
    session: Session,
    *,
    authenticated_owner_id: str,
    snapshot: OrderSnapshot,
    confirmation_key: str,
) -> Order:
    """Atomically persist and return one immutable order snapshot.

    ``authenticated_owner_id`` must come from the validated server session,
    never a request body. The snapshot cannot carry an owner ID. A fresh
    Session is required because this method owns and commits its transaction.
    Unique-number collision retries belong to T029, which generates numbers.
    """
    owner_id = str(UUID(authenticated_owner_id))
    key = str(UUID(confirmation_key))
    snapshot.validate_contract()
    address = snapshot.delivery_address
    record = OrderRecord(
        id=str(snapshot.id),
        order_number=snapshot.order_number,
        user_id=owner_id,
        created_at=snapshot.created_at.astimezone(UTC),
        status=OrderStatus.REGISTERED.value,
        payment_method="simulated",
        payment_status="not_processed",
        recipient_name=address.recipient_name,
        phone=address.phone,
        county=address.county,
        locality=address.locality,
        street_address=address.street_address,
        building=address.building,
        entrance=address.entrance,
        floor=address.floor,
        apartment=address.apartment,
        postal_code=address.postal_code,
        country_code=address.country_code,
        subtotal_bani=snapshot.subtotal_bani,
        shipping_bani=snapshot.shipping_bani,
        total_bani=snapshot.total_bani,
        items=[
            OrderItemRecord(
                position=position,
                product_id=str(item.product_id),
                sku=item.sku,
                name=item.name,
                image_url=str(item.image_url) if item.image_url is not None else None,
                unit_price_bani=item.unit_price_bani,
                quantity=item.quantity,
                line_total_bani=item.line_total_bani,
            )
            for position, item in enumerate(snapshot.items)
        ],
    )

    with session.begin():
        prior = get_order_by_confirmation(
            session, authenticated_owner_id=owner_id, confirmation_key=key
        )
        if prior is not None:
            return prior
        session.add(record)
        # Persist the order header and its item snapshots before the separate
        # idempotency row so its order_id foreign key is valid on SQLite.
        session.flush()
        session.add(OrderConfirmationRecord(
            user_id=owner_id, confirmation_key=key, order_id=str(snapshot.id)
        ))
        session.flush()
        result = _to_domain(record)
    return result


def get_order_by_confirmation(
    session: Session, *, authenticated_owner_id: str, confirmation_key: str
) -> Order | None:
    """Resolve a replay key only within its authenticated customer's namespace."""
    owner_id = str(UUID(authenticated_owner_id))
    key = str(UUID(confirmation_key))
    record = session.scalar(
        select(OrderRecord)
        .join(OrderConfirmationRecord, OrderConfirmationRecord.order_id == OrderRecord.id)
        .where(
            OrderConfirmationRecord.user_id == owner_id,
            OrderConfirmationRecord.confirmation_key == key,
            OrderRecord.user_id == owner_id,
        )
        .options(selectinload(OrderRecord.items))
    )
    return _to_domain(record) if record is not None else None


def list_orders(session: Session, *, authenticated_owner_id: str) -> list[Order]:
    """Return only this authenticated customer's orders, newest first."""
    owner_id = str(UUID(authenticated_owner_id))
    records = session.scalars(
        select(OrderRecord)
        .where(OrderRecord.user_id == owner_id)
        .options(selectinload(OrderRecord.items))
        .order_by(OrderRecord.created_at.desc(), OrderRecord.id.desc())
    ).all()
    return [_to_domain(record) for record in records]


def get_order(
    session: Session,
    *,
    authenticated_owner_id: str,
    order_id: UUID,
) -> Order | None:
    """Read an order only when both its ID and authenticated owner match."""
    owner_id = str(UUID(authenticated_owner_id))
    record = session.scalar(
        select(OrderRecord)
        .where(OrderRecord.id == str(order_id), OrderRecord.user_id == owner_id)
        .options(selectinload(OrderRecord.items))
    )
    return _to_domain(record) if record is not None else None


def get_order_by_number(
    session: Session,
    *,
    authenticated_owner_id: str,
    order_number: str,
) -> Order | None:
    """Read an order by its public number only inside its authenticated owner's scope."""
    owner_id = str(UUID(authenticated_owner_id))
    record = session.scalar(
        select(OrderRecord)
        .where(OrderRecord.order_number == order_number, OrderRecord.user_id == owner_id)
        .options(selectinload(OrderRecord.items))
    )
    return _to_domain(record) if record is not None else None


def _as_utc(value: datetime) -> datetime:
    """Normalize SQLite's naive UTC values back to timezone-aware UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _to_domain(record: OrderRecord) -> Order:
    """Materialize API/domain data exclusively from persisted snapshots."""
    return Order.model_validate(
        {
            "id": record.id,
            "order_number": record.order_number,
            "customer_id": record.user_id,
            "created_at": _as_utc(record.created_at),
            "status": OrderStatus(record.status),
            "payment": MockPaymentState(
                method=record.payment_method,
                status=record.payment_status,
            ),
            "delivery_address": {
                "recipient_name": record.recipient_name,
                "phone": record.phone,
                "county": record.county,
                "locality": record.locality,
                "street_address": record.street_address,
                "building": record.building,
                "entrance": record.entrance,
                "floor": record.floor,
                "apartment": record.apartment,
                "postal_code": record.postal_code,
                "country_code": record.country_code,
            },
            "items": [
                {
                    "product_id": item.product_id,
                    "sku": item.sku,
                    "name": item.name,
                    "image_url": item.image_url,
                    "unit_price_bani": item.unit_price_bani,
                    "quantity": item.quantity,
                    "line_total_bani": item.line_total_bani,
                }
                for item in record.items
            ],
            "subtotal_bani": record.subtotal_bani,
            "shipping_bani": record.shipping_bani,
            "total_bani": record.total_bani,
        }
    )
