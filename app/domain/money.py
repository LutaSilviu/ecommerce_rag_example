"""Exact RON money helpers shared by catalog, cart, and order code.

Amounts are stored as integer bani (100 bani = 1 RON).  The module only uses
Python's standard library so callers can use it without loading the app or
its optional dependencies.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TypeAlias


MoneyInput: TypeAlias = Decimal | int | str
BANI_PER_RON = 100
CURRENCY_CODE = "RON"


def validate_bani(amount_bani: int, *, allow_negative: bool = False) -> int:
    """Return an integer-bani amount or raise for invalid money values.

    ``bool`` is rejected explicitly even though it is a subclass of ``int``.
    Prices and order totals are non-negative by default; callers handling a
    refund or adjustment can opt into negative values.
    """
    if isinstance(amount_bani, bool) or not isinstance(amount_bani, int):
        raise TypeError("amount_bani must be an integer number of bani")
    if amount_bani < 0 and not allow_negative:
        raise ValueError("amount_bani cannot be negative")
    return amount_bani


def ron_to_bani(amount_ron: MoneyInput, *, allow_negative: bool = False) -> int:
    """Convert a decimal RON amount to bani, rounding half up to one ban.

    Accepts ``Decimal``, integer, or a decimal string. Floats are intentionally
    unsupported because their binary representation can make monetary
    rounding surprising. More than two fractional decimal places are rounded
    with ``ROUND_HALF_UP`` (e.g. ``"1.235"`` becomes 124 bani).
    """
    if isinstance(amount_ron, bool) or isinstance(amount_ron, float):
        raise TypeError("amount_ron must be Decimal, int, or decimal string; floats are not allowed")
    if not isinstance(amount_ron, (Decimal, int, str)):
        raise TypeError("amount_ron must be Decimal, int, or decimal string")
    try:
        value = Decimal(amount_ron)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount_ron must be a finite decimal amount") from exc
    if not value.is_finite():
        raise ValueError("amount_ron must be finite")
    if value < 0 and not allow_negative:
        raise ValueError("amount_ron cannot be negative")

    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    bani = int(rounded * BANI_PER_RON)
    return validate_bani(bani, allow_negative=allow_negative)


def add_bani(*amounts_bani: int) -> int:
    """Add validated non-negative bani amounts without converting to RON."""
    return sum(validate_bani(amount) for amount in amounts_bani)


def multiply_bani(unit_amount_bani: int, quantity: int) -> int:
    """Calculate an exact line total from a unit price and whole quantity."""
    unit_amount_bani = validate_bani(unit_amount_bani)
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    return unit_amount_bani * quantity


def format_ron(amount_bani: int, *, include_currency: bool = True) -> str:
    """Format bani using Romanian separators (``1.234,56 RON``).

    Grouping uses a period and the decimal separator is a comma. Formatting
    never passes through floating-point arithmetic.
    """
    amount_bani = validate_bani(amount_bani, allow_negative=True)
    sign = "-" if amount_bani < 0 else ""
    whole, fractional = divmod(abs(amount_bani), BANI_PER_RON)
    grouped = f"{whole:,}".replace(",", ".")
    rendered = f"{sign}{grouped},{fractional:02d}"
    return f"{rendered} {CURRENCY_CODE}" if include_currency else rendered
