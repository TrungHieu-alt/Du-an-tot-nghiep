"""Unit tests for backend/v2_search/.

Covers:
  * embed_query: shape, empty input, token-order independence,
    parity with the underlying embed_text (no drift).
  * vector_to_pg_literal: format contract used by SQL builders.
"""

from __future__ import annotations

import math
import unittest

from db_v2.scenario.embedder import embed_text
from v2_search import embed_query, vector_to_pg_literal


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class EmbedQueryTests(unittest.TestCase):
    def test_returns_list_of_384_floats(self):
        vec = embed_query("python docker kubernetes")
        self.assertIsInstance(vec, list)
        self.assertEqual(len(vec), 384)
        for v in vec:
            self.assertIsInstance(v, float)

    def test_empty_input_returns_zero_vector(self):
        vec = embed_query("")
        self.assertEqual(len(vec), 384)
        self.assertTrue(all(v == 0.0 for v in vec))

    def test_whitespace_only_input_returns_zero_vector(self):
        vec = embed_query("    ")
        self.assertEqual(len(vec), 384)
        self.assertTrue(all(v == 0.0 for v in vec))

    def test_token_order_independent(self):
        # Hash-based embedder L2-normalizes the SUM of per-token vectors,
        # so token order does not affect output (set-of-tokens semantics).
        a = embed_query("senior backend engineer")
        b = embed_query("backend engineer senior")
        sim = _cosine(a, b)
        self.assertAlmostEqual(sim, 1.0, places=6)

    def test_case_insensitive(self):
        a = embed_query("DevOps")
        b = embed_query("devops")
        sim = _cosine(a, b)
        self.assertAlmostEqual(sim, 1.0, places=6)

    def test_distinct_queries_are_not_identical(self):
        a = embed_query("python backend")
        b = embed_query("react frontend")
        sim = _cosine(a, b)
        # Different vocabularies → not identical (sanity check; exact value
        # depends on hash, but should be < 1.0 by a clear margin).
        self.assertLess(sim, 0.99)

    def test_parity_with_underlying_embed_text(self):
        """Regression: the wrapper must not drift from the seed embedder.

        Same algorithm produced the stored embeddings in
        job_embeddings_v2/candidate_embeddings_v2 via embed_text. If
        embed_query ever diverges, retrieval would silently degrade.
        """
        text = "kubernetes cloud aws devops"
        wrapped = embed_query(text)
        direct = embed_text(text).tolist()
        self.assertEqual(wrapped, direct)

    def test_unit_norm_for_non_empty_input(self):
        vec = embed_query("python")
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=5)


class VectorToPgLiteralTests(unittest.TestCase):
    def test_simple_pair(self):
        self.assertEqual(vector_to_pg_literal([0.1, 0.2]), "[0.1,0.2]")

    def test_empty_list(self):
        self.assertEqual(vector_to_pg_literal([]), "[]")

    def test_no_whitespace_in_output(self):
        s = vector_to_pg_literal([0.1, 0.2, 0.3])
        self.assertNotIn(" ", s)

    def test_handles_int_input_by_coercing_to_float(self):
        # Robustness: callers may pass ints accidentally.
        self.assertEqual(vector_to_pg_literal([1, 2]), "[1.0,2.0]")

    def test_long_vector_round_trip_shape(self):
        vec = embed_query("backend")
        literal = vector_to_pg_literal(vec)
        self.assertTrue(literal.startswith("["))
        self.assertTrue(literal.endswith("]"))
        # 384 numbers separated by 383 commas → 384 segments
        body = literal[1:-1]
        self.assertEqual(body.count(",") + 1, 384)


if __name__ == "__main__":
    unittest.main()
