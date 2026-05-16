"""Deterministic local hash embedding provider (Slice 0 baseline).

Wraps `modules.matching.embedding.embed_text` behind the `EmbeddingProvider`
Protocol. No network calls, reproducible across runs. Used as default and
whenever production provider env vars are absent.
"""
from __future__ import annotations

from jobconnect.integrations.embedding.base import EMBEDDING_DIM
from jobconnect.modules.matching.embedding import embed_text


class LocalHashEmbeddingProvider:
    """Deterministic SHA-256-seeded bag-of-words embedding."""

    embedding_version: str = "hash-v1"
    dim: int = EMBEDDING_DIM

    def embed(self, text: str) -> list[float]:
        return embed_text(text, dim=self.dim).tolist()
