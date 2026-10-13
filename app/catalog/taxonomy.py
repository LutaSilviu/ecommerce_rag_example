"""Stable Romanian catalog taxonomy and product field guidance.

Category slugs and availability values are machine-facing identifiers. Romanian
names and labels are presentation content and may be edited without changing
those identifiers. Category-specific attributes are optional metadata; the
canonical product shape remains ``app.domain.models.Product``.
"""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class CategoryDefinition:
    """One seed category with stable slug and localized storefront copy."""

    slug: str
    name_ro: str
    description_ro: str
    sort_order: int


CATEGORIES: tuple[CategoryDefinition, ...] = (
    CategoryDefinition(
        slug="electronics",
        name_ro="Electronice",
        description_ro="Telefoane, accesorii și gadgeturi pentru zi de zi.",
        sort_order=10,
    ),
    CategoryDefinition(
        slug="home",
        name_ro="Casă și grădină",
        description_ro="Obiecte practice și decor pentru locuință.",
        sort_order=20,
    ),
    CategoryDefinition(
        slug="fashion",
        name_ro="Modă",
        description_ro="Îmbrăcăminte și accesorii pentru toate zilele.",
        sort_order=30,
    ),
    CategoryDefinition(
        slug="personal-care",
        name_ro="Îngrijire personală",
        description_ro="Produse pentru îngrijire și rutină personală.",
        sort_order=40,
    ),
    CategoryDefinition(
        slug="sports",
        name_ro="Sport și activități în aer liber",
        description_ro="Echipamente și accesorii pentru mișcare, antrenament și aventuri afară.",
        sort_order=50,
    ),
    CategoryDefinition(
        slug="toys",
        name_ro="Jucării și jocuri",
        description_ro="Jocuri creative și jucării pentru timpul petrecut împreună.",
        sort_order=60,
    ),
    CategoryDefinition(
        slug="books",
        name_ro="Cărți și papetărie",
        description_ro="Lecturi, agende și accesorii pentru idei și proiecte noi.",
        sort_order=70,
    ),
    CategoryDefinition(
        slug="kitchen",
        name_ro="Bucătărie",
        description_ro="Ustensile și accesorii practice pentru pregătirea mesei.",
        sort_order=80,
    ),
)

CATEGORY_BY_SLUG: Mapping[str, CategoryDefinition] = MappingProxyType(
    {category.slug: category for category in CATEGORIES}
)


class ProductAvailability(StrEnum):
    """Derived availability values; stock remains the persisted domain source."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"


AVAILABILITY_LABELS_RO: Mapping[ProductAvailability, str] = MappingProxyType(
    {
        ProductAvailability.IN_STOCK: "În stoc",
        ProductAvailability.OUT_OF_STOCK: "Stoc epuizat",
        ProductAvailability.UNAVAILABLE: "Indisponibil",
    }
)


def availability_for(*, is_active: bool, stock_quantity: int) -> ProductAvailability:
    """Return UI availability from the active flag and non-negative stock count."""

    if stock_quantity < 0:
        raise ValueError("stock_quantity must be non-negative")
    if not is_active:
        return ProductAvailability.UNAVAILABLE
    if stock_quantity == 0:
        return ProductAvailability.OUT_OF_STOCK
    return ProductAvailability.IN_STOCK


@dataclass(frozen=True, slots=True)
class ProductFieldRule:
    """Field contract separated into model and published-listing requirements."""

    field: str
    required_by_model: bool
    required_for_seed_listing: bool
    notes: str


# These names mirror Product in app/domain/models.py. Seed listings should be
# complete enough for SPEC.md's cards/details, even where the domain model allows
# an omitted value (e.g. description or image_url).
PRODUCT_FIELD_RULES: tuple[ProductFieldRule, ...] = (
    ProductFieldRule("id", True, True, "Stable UUID product identifier."),
    ProductFieldRule("sku", True, True, "Unique store SKU; never use a translated name as the identifier."),
    ProductFieldRule("category_id", True, True, "References a Category UUID; category slug is stable content metadata."),
    ProductFieldRule("name", True, True, "Romanian product title, 1–200 characters."),
    ProductFieldRule("description", False, True, "Romanian product details; model defaults to an empty string."),
    ProductFieldRule("price_bani", True, True, "Non-negative integer bani; RON is a display format."),
    ProductFieldRule("image_url", False, True, "Project-owned or usage-cleared image URL; model permits null."),
    ProductFieldRule("stock_quantity", False, True, "Non-negative integer; model defaults to zero."),
    ProductFieldRule("is_active", False, True, "Whether the listing is visible; model defaults to true."),
)


# Optional category-specific descriptive metadata. These keys do not alter the
# canonical Product model or participate in price, stock, cart, or order rules.
CATEGORY_ATTRIBUTE_RULES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "electronics": ("brand", "color", "warranty_months", "connectivity"),
        "home": ("material", "color", "dimensions", "room"),
        "fashion": ("brand", "color", "size", "material"),
        "personal-care": ("brand", "volume_ml", "skin_type", "ingredients_highlights"),
    }
)


@dataclass(frozen=True, slots=True)
class ImageGuidance:
    """Recommended crop guidance for consistent catalog presentation."""

    card_aspect_ratio: str
    detail_aspect_ratio: str
    fit: str
    notes: str


IMAGE_GUIDANCE = ImageGuidance(
    card_aspect_ratio="4:3",
    detail_aspect_ratio="4:3",
    fit="contain",
    notes=(
        "Use a consistent 4:3 source/canvas for cards and details; contain the full "
        "product on a neutral background and avoid cropping labels or product edges."
    ),
)
