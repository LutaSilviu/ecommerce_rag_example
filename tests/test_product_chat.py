"""Focused tests for semantic catalog retrieval and API-key handling."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.chat import service
from app.chat.routes import router
from app.catalog.repository import CatalogProduct, CatalogCategory
from app.persistence.base import Base
from app.persistence.catalog_models import CatalogCategoryRecord, CatalogProductRecord


class FakeEmbeddings:
    def __init__(self):
        self.calls = []

    @staticmethod
    def vector(text):
        normalized = text.casefold()
        if any(word in normalized for word in ("telefon", "smartphone", "mobile", "încărcător", "incarcator")):
            return [1.0, 0.0, 0.0]
        if any(word in normalized for word in ("carte", "roman", "lectură", "lectura")):
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def create(self, *, model, input):
        self.calls.append((model, list(input)))
        return SimpleNamespace(
            data=[SimpleNamespace(index=i, embedding=self.vector(text)) for i, text in enumerate(input)]
        )


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.category_id = UUID("a1000000-0000-4000-8000-000000000001")
        self.products = (
            CatalogProduct(
                id=UUID("b2000000-0000-4000-8000-000000000001"), sku="NM-ELE-001",
                slug="incarcator", category_id=self.category_id, name="Încărcător rapid",
                description="Încărcător pentru telefon mobil și tabletă.", price_bani=12990,
                stock_quantity=4,
            ),
            CatalogProduct(
                id=UUID("b2000000-0000-4000-8000-000000000002"), sku="NM-BOK-001",
                slug="roman", category_id=self.category_id, name="Roman ilustrat",
                description="Carte pentru lectură și relaxare.", price_bani=4990,
                stock_quantity=8,
            ),
        )
        self.category = CatalogCategory(id=self.category_id, slug="demo", name="Demo")
        self.catalog = SimpleNamespace(
            list_products=lambda: self.products,
            list_categories=lambda: (self.category,),
        )
        self.embeddings = FakeEmbeddings()
        self.client = SimpleNamespace(embeddings=self.embeddings)
        self.patches = [
            patch.object(service, "catalog", self.catalog),
            patch.object(service, "get_session_factory", lambda: self.sessions),
            patch.object(service, "get_settings", return_value=SimpleNamespace(openai_embedding_model="fake-embedding")),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.engine.dispose()

    def test_semantic_search_matches_paraphrase_and_uses_live_stock_price(self):
        result = service.retrieve_catalog_context("accesoriu pentru smartphone", self.client)
        self.assertEqual([item["name"] for item in result], ["Încărcător rapid"])
        self.assertEqual(result[0]["price"], "129,90 RON")
        self.assertEqual(result[0]["stock_quantity"], 4)

    def test_unrelated_question_has_no_catalog_matches(self):
        self.assertEqual(service.retrieve_catalog_context("vremea de mâine", self.client), [])

    def test_phone_request_without_a_phone_returns_only_related_in_stock_electronics(self):
        result = service._related_catalog_context(
            "vreau telefon cu 4 gb ram",
            self.products,
            {str(self.category_id): "Electronice"},
        )
        self.assertEqual([item["name"] for item in result], [self.products[0].name])
        self.assertEqual(result[0]["match_type"], "related_alternative")
        self.assertEqual(result[0]["stock_quantity"], 4)

    def test_ram_size_is_compared_with_catalog_specs(self):
        product = {"name": "Telefon demo", "description": "Telefon cu 8 GB RAM"}
        self.assertTrue(service._requested_ram_spec_missing("telefon cu 4 gb ram", [product]))
        self.assertFalse(service._requested_ram_spec_missing("telefon cu 8 gb ram", [product]))

    def test_product_vectors_are_cached_across_questions(self):
        service.retrieve_catalog_context("smartphone", self.client)
        first_calls = list(self.embeddings.calls)
        service.retrieve_catalog_context("telefon mobil", self.client)
        self.assertEqual([len(inputs) for _, inputs in first_calls], [2, 1])
        # The second request embeds only its query; product vectors came from SQLite.
        self.assertEqual([len(inputs) for _, inputs in self.embeddings.calls], [2, 1, 1])

    def test_changed_catalog_text_invalidates_only_that_vector(self):
        service.retrieve_catalog_context("smartphone", self.client)
        self.products = (
            self.products[0].model_copy(update={"description": "Încărcător compatibil cu telefon și tabletă."}),
            self.products[1],
        )
        service.retrieve_catalog_context("smartphone", self.client)
        self.assertEqual([len(inputs) for _, inputs in self.embeddings.calls], [2, 1, 1, 1])

    def test_response_uses_responses_api_with_retrieved_catalog(self):
        fake_response = SimpleNamespace(output_text="Încărcătorul este 129,90 RON și sunt 4 bucăți în stoc.")
        responses = SimpleNamespace(create=unittest.mock.Mock(return_value=fake_response))
        client = SimpleNamespace(responses=responses)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only-key"}):
            with patch.object(service, "OpenAI", return_value=client):
                with patch.object(service, "retrieve_catalog_context", return_value=[{"name": "Încărcător rapid", "price": "129,90 RON", "stock_quantity": 4}]):
                    with patch.object(service, "get_settings", return_value=SimpleNamespace(openai_model="test-model")):
                        answer = service.answer_from_catalog("Cât costă?", [])
        self.assertIn("129,90 RON", answer)
        kwargs = responses.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "test-model")
        self.assertFalse(kwargs["store"])
        self.assertIn("exclusiv", kwargs["instructions"])
        self.assertIn("Exemplul 2", kwargs["instructions"])
        self.assertIn("Nu avem telefoane cu 4 GB RAM", kwargs["instructions"])
        self.assertIn("Încărcător rapid", kwargs["input"][0]["content"])

    def test_missing_api_key_has_clear_configuration_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(service.ChatConfigurationError, "OPENAI_API_KEY"):
                service.answer_from_catalog("Cât costă produsul?", [])


class ChatRouteTests(unittest.TestCase):
    def test_chat_request_is_validated_and_response_is_wrapped(self):
        app = FastAPI()
        app.include_router(router)
        with patch("app.chat.routes.answer_from_catalog", return_value="Produsul costă 12,00 RON."):
            with TestClient(app) as client:
                response = client.post("/api/v1/chat", json={"message": "  Cât costă produsul? "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "Produsul costă 12,00 RON."})

    def test_blank_message_is_rejected(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client:
            response = client.post("/api/v1/chat", json={"message": "  "})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
