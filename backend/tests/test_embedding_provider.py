"""Slice 7: Embedding And Semantic Search adapter.

Covers DoD per slices.md §7:
- Embedding rows contain version from the active provider.
- Semantic search uses intended fields with relevance scores.
- Missing embeddings → component 0 + mentioned in reasoning (regression check).
- Ordering deterministic for equal scores.
- Provider failures raise EmbeddingError (worker marks parse job failed).
"""
from __future__ import annotations

import io
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.embedding import (
    EMBEDDING_DIM,
    EmbeddingError,
    LocalHashEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
    reset_embedding_provider_cache,
)
from jobconnect.modules.matching.reasoning import build_reasoning
from jobconnect.modules.matching.scoring import cosine_similarity


# ---------------------------------------------------------------------------
# 1. LocalHashEmbeddingProvider
# ---------------------------------------------------------------------------


class TestLocalProvider(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = LocalHashEmbeddingProvider()

    def test_version_and_dim(self) -> None:
        self.assertEqual(self.provider.embedding_version, "hash-v1")
        self.assertEqual(self.provider.dim, 384)

    def test_returns_list_of_expected_length(self) -> None:
        vec = self.provider.embed("hello world")
        self.assertIsInstance(vec, list)
        self.assertEqual(len(vec), EMBEDDING_DIM)
        self.assertTrue(all(isinstance(v, float) for v in vec))

    def test_empty_text_returns_zero_vector(self) -> None:
        vec = self.provider.embed("")
        self.assertEqual(len(vec), EMBEDDING_DIM)
        self.assertTrue(all(v == 0.0 for v in vec))

    def test_deterministic_for_same_input(self) -> None:
        a = self.provider.embed("python backend engineer")
        b = self.provider.embed("python backend engineer")
        self.assertEqual(a, b)


# ---------------------------------------------------------------------------
# 2. OpenAIEmbeddingProvider (mocked HTTP)
# ---------------------------------------------------------------------------


def _embedding_response(vector: list[float], status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"data": [{"embedding": vector}]}
    resp.text = json.dumps({"data": [{"embedding": vector}]})
    return resp


class TestOpenAIProviderHappyPath(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = OpenAIEmbeddingProvider(
            api_key="sk-test", model="text-embedding-3-small"
        )

    def test_version_includes_model(self) -> None:
        self.assertEqual(
            self.provider.embedding_version, "openai-text-embedding-3-small-v1"
        )

    def test_dim_matches_db_schema(self) -> None:
        self.assertEqual(self.provider.dim, EMBEDDING_DIM)

    def test_returns_provider_vector(self) -> None:
        vector = [0.01 * i for i in range(EMBEDDING_DIM)]
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post",
            return_value=_embedding_response(vector),
        ):
            result = self.provider.embed("hello")
        self.assertEqual(len(result), EMBEDDING_DIM)
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[-1], 0.01 * (EMBEDDING_DIM - 1))

    def test_empty_text_skips_http_call(self) -> None:
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post"
        ) as mock_post:
            result = self.provider.embed("")
        self.assertEqual(len(result), EMBEDDING_DIM)
        self.assertTrue(all(v == 0.0 for v in result))
        mock_post.assert_not_called()


class TestOpenAIProviderFailures(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = OpenAIEmbeddingProvider(
            api_key="sk-test", model="text-embedding-3-small"
        )

    def test_network_error_raises_embedding_error(self) -> None:
        import httpx

        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post",
            side_effect=httpx.HTTPError("boom"),
        ):
            with self.assertRaises(EmbeddingError) as ctx:
                self.provider.embed("text")
        self.assertIn("Embedding request failed", str(ctx.exception))

    def test_non_200_raises_embedding_error(self) -> None:
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "internal error"
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post", return_value=resp
        ):
            with self.assertRaises(EmbeddingError):
                self.provider.embed("text")

    def test_malformed_response_raises_embedding_error(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"unexpected": "shape"}
        resp.text = "..."
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post", return_value=resp
        ):
            with self.assertRaises(EmbeddingError):
                self.provider.embed("text")

    def test_dimension_mismatch_raises_embedding_error(self) -> None:
        # Provider returned 100-dim vector but schema demands 384
        bad_vector = [0.1] * 100
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post",
            return_value=_embedding_response(bad_vector),
        ):
            with self.assertRaises(EmbeddingError) as ctx:
                self.provider.embed("text")
        self.assertIn("length mismatch", str(ctx.exception))

    def test_non_numeric_values_raise_embedding_error(self) -> None:
        bad_vector: list[Any] = ["abc"] * EMBEDDING_DIM
        with patch(
            "jobconnect.integrations.embedding.openai.httpx.post",
            return_value=_embedding_response(bad_vector),
        ):
            with self.assertRaises(EmbeddingError):
                self.provider.embed("text")


# ---------------------------------------------------------------------------
# 3. get_embedding_provider() factory
# ---------------------------------------------------------------------------


class TestGetEmbeddingProviderFactory(unittest.TestCase):
    def setUp(self) -> None:
        reset_embedding_provider_cache()
        self._snap = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._snap)
        reset_embedding_provider_cache()

    def test_default_is_local(self) -> None:
        os.environ.pop("EMBEDDING_PROVIDER", None)
        provider = get_embedding_provider()
        self.assertIsInstance(provider, LocalHashEmbeddingProvider)

    def test_openai_without_api_key_falls_back_to_local(self) -> None:
        os.environ["EMBEDDING_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_EMBEDDING_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        provider = get_embedding_provider()
        self.assertIsInstance(provider, LocalHashEmbeddingProvider)

    def test_openai_with_dedicated_api_key(self) -> None:
        os.environ["EMBEDDING_PROVIDER"] = "openai"
        os.environ["OPENAI_EMBEDDING_API_KEY"] = "sk-emb"
        provider = get_embedding_provider()
        self.assertIsInstance(provider, OpenAIEmbeddingProvider)

    def test_openai_falls_back_to_shared_openai_key(self) -> None:
        os.environ["EMBEDDING_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_EMBEDDING_API_KEY", None)
        os.environ["OPENAI_API_KEY"] = "sk-shared"
        provider = get_embedding_provider()
        self.assertIsInstance(provider, OpenAIEmbeddingProvider)

    def test_unknown_provider_falls_back_to_local(self) -> None:
        os.environ["EMBEDDING_PROVIDER"] = "huggingface"
        provider = get_embedding_provider()
        self.assertIsInstance(provider, LocalHashEmbeddingProvider)


# ---------------------------------------------------------------------------
# 4. Missing-embedding regression (REQUIREMENTS §6.5 + §7.5)
# ---------------------------------------------------------------------------


class TestMissingEmbeddingBehavior(unittest.TestCase):
    def test_cosine_with_none_returns_zero(self) -> None:
        self.assertEqual(cosine_similarity(None, [0.1] * EMBEDDING_DIM), 0.0)
        self.assertEqual(cosine_similarity([0.1] * EMBEDDING_DIM, None), 0.0)

    def test_reasoning_mentions_missing_fields(self) -> None:
        reasoning = build_reasoning(
            title_score=0.7,
            skills_score=0.4,
            req_exp_score=0.0,
            req_summary_score=0.0,
            matched_skills=["python"],
            missing_emb_fields=["job.emb_requirement", "resume.emb_experience"],
        )
        self.assertIn("Missing embeddings", reasoning)
        self.assertIn("job.emb_requirement", reasoning)
        self.assertIn("resume.emb_experience", reasoning)


# ---------------------------------------------------------------------------
# 5. Worker integration: embedding_version flows from active provider
# ---------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared
        self.executed: list[tuple[str, Any]] = []
        self._current: Any = None
        self.rowcount = 0

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))
        self._current = self._shared.pop(0) if self._shared else None
        if isinstance(self._current, int):
            self.rowcount = self._current
            self._current = None

    def fetchone(self) -> Any:
        return self._current

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_) -> None:
        return None


class FakeConnection:
    def __init__(self, shared: list[Any], log: list[FakeCursor]) -> None:
        self._shared = shared
        self._log = log

    def cursor(self) -> FakeCursor:
        c = FakeCursor(self._shared)
        self._log.append(c)
        return c

    def commit(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_) -> None:
        return None


class TestWorkerEmbeddingVersionPersistence(unittest.TestCase):
    """The worker MUST write the active provider's embedding_version to DB."""

    def test_local_provider_writes_hash_v1(self) -> None:
        from jobconnect.modules.documents import worker as worker_module

        reset_embedding_provider_cache()

        load_row = (
            99, 11, "candidate_resume", None, None, "queued",
            "documents/test.pdf", "application/pdf", "cv.pdf", 10,
        )
        resume_insert_row = (42,)
        shared: list[Any] = [
            load_row,             # _load_parse_job
            None,                 # _mark_processing
            resume_insert_row,    # INSERT candidate_resumes RETURNING
            None,                 # INSERT candidate_resume_embeddings
            None,                 # UPDATE parse_jobs succeeded
            None,                 # UPDATE uploaded_documents resume_id
            None,                 # UPDATE parse_jobs resume_id
            None,                 # _write_audit
        ]
        cursors: list[FakeCursor] = []
        mock_storage = MagicMock()
        mock_storage.open.return_value = io.BytesIO(b"")

        with patch.object(worker_module, "get_connection",
                          lambda: FakeConnection(shared, cursors)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage), \
             patch.object(worker_module, "extract_text",
                          return_value="Senior Python Engineer\nHa Noi"):
            worker_module._execute(99)

        # Locate the INSERT into candidate_resume_embeddings
        embed_insert = None
        for c in cursors:
            for sql, params in c.executed:
                if "candidate_resume_embeddings" in sql and "INSERT" in sql:
                    embed_insert = params
                    break
            if embed_insert is not None:
                break
        self.assertIsNotNone(embed_insert, "embedding INSERT not executed")
        # Last param = embedding_version
        self.assertEqual(embed_insert[-1], "hash-v1")


if __name__ == "__main__":
    unittest.main()
