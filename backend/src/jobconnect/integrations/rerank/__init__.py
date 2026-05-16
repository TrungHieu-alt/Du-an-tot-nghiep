from __future__ import annotations

from functools import lru_cache

from .base import RerankError, RerankProvider
from .local import LocalCrossEncoderRerankProvider, preload_local_rerank_model


@lru_cache(maxsize=1)
def get_rerank_provider() -> RerankProvider:
    return LocalCrossEncoderRerankProvider()


def reset_rerank_provider_cache() -> None:
    get_rerank_provider.cache_clear()


__all__ = [
    "RerankError",
    "RerankProvider",
    "LocalCrossEncoderRerankProvider",
    "get_rerank_provider",
    "reset_rerank_provider_cache",
    "preload_local_rerank_model",
]
