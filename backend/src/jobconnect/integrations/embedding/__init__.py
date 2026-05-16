"""Embedding provider selection.

Runtime selects an implementation via the `EMBEDDING_PROVIDER` env var:
- `local` (default) → deterministic SHA-256 hash provider (no network).
- `openai`          → OpenAI-compatible `/v1/embeddings`; requires API key.

If `EMBEDDING_PROVIDER=openai` is requested but no API key is set
(`OPENAI_EMBEDDING_API_KEY` or `OPENAI_API_KEY`), the factory logs a warning
and falls back to local so dev/test environments stay runnable.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

from .base import EMBEDDING_DIM, EmbeddingError, EmbeddingProvider
from .local import LocalHashEmbeddingProvider
from .openai import OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    if provider == "openai":
        api_key = (
            os.getenv("OPENAI_EMBEDDING_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )
        if not api_key:
            logger.warning(
                "EMBEDDING_PROVIDER=openai but no API key set; falling back to local."
            )
            return LocalHashEmbeddingProvider()
        return OpenAIEmbeddingProvider(api_key=api_key)
    if provider != "local":
        logger.warning(
            "Unknown EMBEDDING_PROVIDER=%r; falling back to local.", provider
        )
    return LocalHashEmbeddingProvider()


def reset_embedding_provider_cache() -> None:
    """Test helper: clear the cached adapter so env overrides take effect."""
    get_embedding_provider.cache_clear()


__all__ = [
    "EMBEDDING_DIM",
    "EmbeddingError",
    "EmbeddingProvider",
    "LocalHashEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider",
    "reset_embedding_provider_cache",
]
