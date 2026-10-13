"""Create persistent catalog tables.

Revision ID: 0001_catalog_tables
Revises:
Create Date: 2026-10-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_catalog_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("sort_order >= 0", name="ck_catalog_categories_sort_order"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_catalog_categories_slug"),
    )
    op.create_table(
        "catalog_products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=False),
        sa.Column("price_bani", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("price_bani >= 0", name="ck_catalog_products_price"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_catalog_products_stock"),
        sa.ForeignKeyConstraint(["category_id"], ["catalog_categories.id"], name="fk_catalog_products_category_id_catalog_categories", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku", name="uq_catalog_products_sku"),
        sa.UniqueConstraint("slug", name="uq_catalog_products_slug"),
    )
    op.create_index("ix_catalog_products_category_id", "catalog_products", ["category_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_catalog_products_category_id", table_name="catalog_products")
    op.drop_table("catalog_products")
    op.drop_table("catalog_categories")
