from __future__ import annotations

from typing import Protocol


class RerankError(Exception):
    """Raised when reranking cannot be completed."""


class RerankProvider(Protocol):
    model_version: str

    def score(self, query: str, documents: list[str]) -> list[float]:
        """Return one relevance score per document in [0, 1]."""
