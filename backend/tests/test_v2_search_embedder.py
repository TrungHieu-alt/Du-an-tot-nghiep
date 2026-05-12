"""Unit tests for backend/v2_search/.

Runtime embeddings must use only local MiniLM. The tests mock the model wrapper
so they do not download model files or call any external service.
"""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from v2_search import embed_query, vector_to_pg_literal
from v2_search.minilm import (
    EMBEDDING_DIM,
    MODEL_NAME,
    MiniLMUnavailableError,
    embed_text_minilm,
    reset_model_cache_for_tests,
)


class EmbedQueryTests(unittest.TestCase):
    def test_returns_list_of_384_floats_from_local_minilm_wrapper(self):
        vector = [0.0] * EMBEDDING_DIM
        vector[0] = 1.0
        with patch("v2_search.embedder.embed_text_minilm", return_value=vector):
            result = embed_query("python docker kubernetes")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), EMBEDDING_DIM)
        for value in result:
            self.assertIsInstance(value, float)

    def test_empty_input_returns_none_without_loading_model(self):
        self.assertIsNone(embed_text_minilm(""))
        self.assertIsNone(embed_text_minilm("    "))

    def test_model_unavailable_error_is_not_hidden(self):
        with patch(
            "v2_search.embedder.embed_text_minilm",
            side_effect=MiniLMUnavailableError("missing local model"),
        ):
            with self.assertRaises(MiniLMUnavailableError):
                embed_query("backend")

    def test_dimension_mismatch_is_rejected(self):
        with patch("v2_search.embedder.embed_text_minilm", return_value=[0.1, 0.2]):
            with self.assertRaises(MiniLMUnavailableError):
                embed_query("backend")


class MiniLMLoaderTests(unittest.TestCase):
    def tearDown(self):
        reset_model_cache_for_tests()

    def test_loads_local_files_only_and_caches_model(self):
        reset_model_cache_for_tests()
        constructed: list[tuple[str, bool]] = []

        class FakeSentenceTransformer:
            def __init__(self, model_name: str, local_files_only: bool = False):
                constructed.append((model_name, local_files_only))

            def encode(self, text: str, normalize_embeddings: bool = False):
                self.last_text = text
                self.normalize_embeddings = normalize_embeddings
                vector = [0.0] * EMBEDDING_DIM
                vector[0] = 1.0
                return vector

        fake_module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
        with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
            first = embed_text_minilm("backend")
            second = embed_text_minilm("frontend")

        self.assertEqual(len(first), EMBEDDING_DIM)
        self.assertEqual(len(second), EMBEDDING_DIM)
        self.assertEqual(constructed, [(MODEL_NAME, True)])

    def test_unavailable_model_raises_without_remote_fallback(self):
        reset_model_cache_for_tests()

        class FailingSentenceTransformer:
            def __init__(self, model_name: str, local_files_only: bool = False):
                self.model_name = model_name
                self.local_files_only = local_files_only
                raise RuntimeError("not cached")

        fake_module = types.SimpleNamespace(SentenceTransformer=FailingSentenceTransformer)
        with patch.dict(sys.modules, {"sentence_transformers": fake_module}):
            with self.assertRaises(MiniLMUnavailableError) as ctx:
                embed_text_minilm("backend")

        self.assertIn("no remote API fallback", str(ctx.exception))


class VectorToPgLiteralTests(unittest.TestCase):
    def test_simple_pair(self):
        self.assertEqual(vector_to_pg_literal([0.1, 0.2]), "[0.1,0.2]")

    def test_empty_list(self):
        self.assertEqual(vector_to_pg_literal([]), "[]")

    def test_no_whitespace_in_output(self):
        rendered = vector_to_pg_literal([0.1, 0.2, 0.3])
        self.assertNotIn(" ", rendered)

    def test_handles_int_input_by_coercing_to_float(self):
        self.assertEqual(vector_to_pg_literal([1, 2]), "[1.0,2.0]")

    def test_long_vector_round_trip_shape(self):
        vector = [0.0] * EMBEDDING_DIM
        literal = vector_to_pg_literal(vector)
        self.assertTrue(literal.startswith("["))
        self.assertTrue(literal.endswith("]"))
        body = literal[1:-1]
        self.assertEqual(body.count(",") + 1, EMBEDDING_DIM)


if __name__ == "__main__":
    unittest.main()
