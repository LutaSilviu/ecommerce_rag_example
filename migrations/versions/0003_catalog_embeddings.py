"""Cache OpenAI semantic vectors for current product text.

Revision ID: 0003_catalog_embeddings
Revises: 0002_catalog_demo_data
Create Date: 2026-10-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_catalog_embeddings"
down_revision = "0002_catalog_demo_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_product_embeddings",
        sa.Column("product_id", sa.String(36), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("vector_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["catalog_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id"),
    )


def downgrade() -> None:
    op.drop_table("catalog_product_embeddings")
