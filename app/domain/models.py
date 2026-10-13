"""Pydantic domain and API contract types.

These models deliberately describe the domain only. Database/ORM mappings belong
in the persistence layer and can adapt to these stable contracts later.
Money is represented in integer bani; localized display strings are a UI concern.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class DomainModel(BaseModel):
    """Common strictness for shared domain contracts."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Category(DomainModel):
    """A stable catalog category; ``name`` is content, not an identifier."""

    id: UUID
    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True


class Product(DomainModel):
    """Catalog product with domain values separate from presentation labels."""

    id: UUID
    sku: str = Field(min_length=1, max_length=64)
    category_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    price_bani: int = Field(ge=0)
    image_url: HttpUrl | None = None
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class CartLine(DomainModel):
    """Client cart input contains identity and quantity, never trusted prices."""

    product_id: UUID
    quantity: int = Field(ge=1, le=99)


class CustomerProfile(DomainModel):
    """Safe public profile fields; excludes password, session, and OAuth secrets."""

    id: UUID
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=120)


class DeliveryAddress(DomainModel):
    """Romanian contact and delivery details, also an immutable order snapshot.

    The customer's account email remains the contact email; it is not duplicated
    into this address snapshot. County and locality are free text so the contract
    supports all Romanian counties and Bucharest without a stale hard-coded list.
    """

    recipient_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=24)
    county: str = Field(min_length=2, max_length=80)
    locality: str = Field(min_length=1, max_length=100)
    street_address: str = Field(min_length=3, max_length=200)
    building: str | None = Field(default=None, max_length=30)
    entrance: str | None = Field(default=None, max_length=30)
    floor: str | None = Field(default=None, max_length=20)
    apartment: str | None = Field(default=None, max_length=20)
    postal_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    country_code: Literal["RO"] = "RO"

    @field_validator("phone")
    @classmethod
    def validate_phone_characters(cls, value: str) -> str:
        """Allow common phone formatting while requiring 7–15 actual digits."""
        allowed = set("0123456789+ ()-.")
        if any(character not in allowed for character in value):
            raise ValueError("phone may contain only digits and common phone separators")
        digit_count = sum(character.isdigit() for character in value)
        if not 7 <= digit_count <= 15:
            raise ValueError("phone must contain between 7 and 15 digits")
        return value


class MockPaymentMethod(StrEnum):
    """The prototype records a simulation only; no payment method is charged."""

    SIMULATED = "simulated"


class MockPaymentStatus(StrEnum):
    NOT_PROCESSED = "not_processed"


class MockPaymentState(DomainModel):
    """Non-transactional payment simulation; carries no card or processor data."""

    method: MockPaymentMethod = MockPaymentMethod.SIMULATED
    status: MockPaymentStatus = MockPaymentStatus.NOT_PROCESSED


class OrderStatus(StrEnum):
    REGISTERED = "registered"


class OrderItemSnapshot(DomainModel):
    """Product details and price as confirmed at order time."""

    product_id: UUID
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    image_url: HttpUrl | None = None
    unit_price_bani: int = Field(ge=0)
    quantity: int = Field(ge=1, le=99)
    line_total_bani: int = Field(ge=0)


class Order(DomainModel):
    """Order aggregate contract with customer, address, and item snapshots."""

    id: UUID
    order_number: str = Field(min_length=1, max_length=40)
    customer_id: UUID
    created_at: datetime
    status: OrderStatus = OrderStatus.REGISTERED
    payment: MockPaymentState
    delivery_address: DeliveryAddress
    items: list[OrderItemSnapshot] = Field(min_length=1)
    subtotal_bani: int = Field(ge=0)
    shipping_bani: int = Field(ge=0)
    total_bani: int = Field(ge=0)
