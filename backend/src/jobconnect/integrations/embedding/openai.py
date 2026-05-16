"""OpenAI-compatible embedding provider.

Calls `/v1/embeddings` with `dimensions=384` (supported by
`text-embedding-3-*` family) so output matches the DB schema `VECTOR(384)`
without migration. If the provider returns a vector of different length, the
adapter raises `EmbeddingError` rather than silently zero-padding.

Failure handling:
- Network / HTTP errors raise `EmbeddingError`.
- Non-2xx responses raise `EmbeddingError`.
- Malformed JSON or missing `embedding` field raises `EmbeddingError`.
- Empty input returns the zero vector without a network call.

Configuration (env vars):
- `OPENAI_EMBEDDING_API_KEY` (falls back to `OPENAI_API_KEY`)
- `OPENAI_EMBEDDING_MODEL`  (default: `text-embedding-3-small`)
- `OPENAI_EMBEDDING_BASE_URL` (default: `https://api.openai.com/v1`)
- `OPENAI_EMBEDDING_TIMEOUT_SECONDS` (default: `30`)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from jobconnect.integrations.embedding.base import EMBEDDING_DIM, EmbeddingError


_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "text-embedding-3-small"
_DEFAULT_TIMEOUT = 30


class OpenAIEmbeddingProvider:
    """OpenAI-compatible embeddings adapter returning 384-dim vectors."""

    dim: int = EMBEDDING_DIM

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model or os.getenv("OPENAI_EMBEDDING_MODEL", _DEFAULT_MODEL)
        self._base_url = (
            base_url or os.getenv("OPENAI_EMBEDDING_BASE_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self._timeout = float(
            timeout_seconds
            if timeout_seconds is not None
            else os.getenv("OPENAI_EMBEDDING_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT)
        )
        self.embedding_version = f"openai-{self._model}-v1"

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self.dim

        url = f"{self._base_url}/embeddings"
        body: dict[str, Any] = {
            "model": self._model,
            "input": text[:8000],
            "dimensions": self.dim,
        }
        try:
            resp = httpx.post(
                url,
                json=body,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise EmbeddingError(
                f"Embedding HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            payload = resp.json()
            vector = payload["data"][0]["embedding"]
        except (KeyError, IndexError, ValueError) as exc:
            raise EmbeddingError(f"Embedding response malformed: {exc}") from exc

        if not isinstance(vector, list) or len(vector) != self.dim:
            raise EmbeddingError(
                f"Embedding length mismatch: expected {self.dim}, got {len(vector) if isinstance(vector, list) else type(vector)}."
            )
        try:
            return [float(v) for v in vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingError(f"Embedding contains non-numeric value: {exc}") from exc
