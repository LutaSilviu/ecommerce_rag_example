"""Authenticated customer order creation endpoint."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.auth.dependencies import get_current_user, get_db
from app.auth.routes import _require_same_origin
from app.domain.models import Order
from app.orders.service import CreateOrderPayload, OrderCreationError, create_customer_order
from app.persistence.models import User
from app.persistence.order_repository import get_order_by_number, list_orders


router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.get("", response_model=list[Order])
def list_customer_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Order]:
    """Return only the authenticated customer's orders, newest first."""
    return list_orders(db, authenticated_owner_id=current_user.id)


@router.get("/{order_number}", response_model=Order)
def get_customer_order(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    """Return a saved order only to its owner; absent and foreign orders look alike."""
    order = get_order_by_number(
        db, authenticated_owner_id=current_user.id, order_number=order_number
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comanda nu a fost găsită.")
    return order


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    request: Request,
    idempotency_key: UUID = Header(alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
) -> Order:
    """Validate and persist a mock order for the cookie-authenticated customer."""
    _require_same_origin(request)
    try:
        payload = CreateOrderPayload.model_validate(await request.json())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Datele comenzii sunt incomplete sau invalide.") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Corpul cererii nu este JSON valid.") from exc

    try:
        return create_customer_order(
            payload,
            authenticated_owner_id=current_user.id,
            confirmation_key=str(idempotency_key),
        )
    except OrderCreationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
