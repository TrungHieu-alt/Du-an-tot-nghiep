from __future__ import annotations

import os
from functools import lru_cache

from sentence_transformers import CrossEncoder

from .base import RerankError

_DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def _load_model(model_name: str) -> CrossEncoder:
    return CrossEncoder(model_name)


class LocalCrossEncoderRerankProvider:
    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or os.getenv("RERANK_MODEL", _DEFAULT_MODEL)
        self.model_version = f"local-{self._model_name}"

    def score(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        pairs = [(query, doc) for doc in documents]
        try:
            raw_scores = _load_model(self._model_name).predict(pairs)
        except Exception as exc:  # pragma: no cover - covered by wrapper tests
            raise RerankError(f"Rerank model failed: {exc}") from exc
        scores: list[float] = []
        for value in raw_scores:
            try:
                f = float(value)
            except (TypeError, ValueError) as exc:
                raise RerankError(f"Rerank score contains non-numeric value: {exc}") from exc
            # CrossEncoder scores are not guaranteed bounded. Clamp for API consistency.
            scores.append(max(0.0, min(1.0, f)))
        return scores


def preload_local_rerank_model() -> None:
    model_name = os.getenv("RERANK_MODEL", _DEFAULT_MODEL)
    _load_model(model_name)
