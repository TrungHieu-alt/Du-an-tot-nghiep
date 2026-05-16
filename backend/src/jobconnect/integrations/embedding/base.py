"""Embedding provider adapter boundary.

Per `docs/mvp-roadmap/provider-strategy.md` Slice 7: vector generation lives
behind a narrow interface so production providers can be swapped without
changing the matching/search call sites. The default is a deterministic local
hash provider (Slice 0 baseline); an OpenAI-compatible provider is enabled via
env vars.

Contract:
- `embed(text)` returns a `list[float]` of length `dim`.
- `dim` is fixed at 384 to match the DB schema (`VECTOR(384)`). Providers that
  cannot produce 384-dim vectors must not be registered.
- `embedding_version` is a stable string persisted onto
  `candidate_resume_embeddings.embedding_version` /
  `job_post_embeddings.embedding_version` for diagnosis and backfill.
- Provider/network errors raise `EmbeddingError`; the worker catches this and
  marks the parse job failed.
"""
from __future__ import annotations

from typing import Protocol


EMBEDDING_DIM: int = 384


class EmbeddingError(Exception):
    """Raised by an embedding adapter when vector generation cannot complete."""


class EmbeddingProvider(Protocol):
    """Adapter interface for text → vector embedding."""

    embedding_version: str
    dim: int

    def embed(self, text: str) -> list[float]:
        """Embed `text` into a `dim`-length vector. Empty text → zero vector."""
