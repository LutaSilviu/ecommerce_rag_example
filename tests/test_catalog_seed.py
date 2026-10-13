"""Regression coverage for stable incremental demo catalog seeds."""

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.catalog.repository import CatalogProduct
from app.catalog.seed import CATEGORY_IDS, PRODUCT_SEEDS, PRODUCT_SLUGS
from app.chat.service import _related_catalog_context
from app.persistence.base import Base
from app.persistence.catalog_models import CatalogProductRecord
from app.persistence import catalog_seed


class CatalogSeedTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()

    def test_8gb_phone_seed_is_stable_and_available_as_related_alternative(self):
        with patch.object(catalog_seed, "get_session_factory", return_value=self.sessions):
            catalog_seed.seed_catalog_data()
            catalog_seed.seed_catalog_data()

        seeded = next(product for product in PRODUCT_SEEDS if PRODUCT_SLUGS[product.id] == "smartphone-echo-8gb")
        self.assertEqual(seeded.sku, "NM-ELE-007")
        self.assertEqual(seeded.category_id, CATEGORY_IDS["electronics"])
        self.assertIn("8 GB RAM", seeded.description)
        self.assertGreater(seeded.price_bani, 0)
        self.assertGreater(seeded.stock_quantity, 0)
        self.assertIsNotNone(seeded.image_url)

        with self.sessions() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(CatalogProductRecord)), len(PRODUCT_SEEDS))
            persisted = session.get(CatalogProductRecord, str(seeded.id))
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.slug, "smartphone-echo-8gb")
            self.assertIn("8 GB RAM", persisted.description)

        product = CatalogProduct.model_validate({**seeded.model_dump(), "slug": PRODUCT_SLUGS[seeded.id]})
        alternatives = _related_catalog_context(
            "vreau telefon cu 4 gb ram", (product,), {str(CATEGORY_IDS["electronics"]): "Electronice"}
        )
        self.assertEqual([item["name"] for item in alternatives], [seeded.name])
        self.assertEqual(alternatives[0]["suggestion_type"], "model")
        self.assertEqual(alternatives[0]["match_type"], "related_alternative")


if __name__ == "__main__":
    unittest.main()
