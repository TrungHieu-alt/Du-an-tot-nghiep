"""Local MiniLM embedding helper.

This module is the only runtime embedding model loader. It uses
`sentence-transformers/all-MiniLM-L6-v2` through the local
`sentence-transformers` package and explicitly disables remote model lookup at
runtime (`local_files_only=True`). There is no OpenAI, Gemini, Cohere, hosted
HuggingFace inference, or other external API fallback.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: Optional[Any] = None
_load_error: Optional[str] = None


class MiniLMUnavailableError(RuntimeError):
    """Raised when the local MiniLM model cannot be loaded from local files."""


def reset_model_cache_for_tests() -> None:
    global _model, _load_error
    _model = None
    _load_error = None


def embed_text_minilm(text: str) -> list[float] | None:
    """Return a local MiniLM embedding, or None for empty input.

    The model is loaded lazily and cached. If the installed model files are not
    available locally, this raises `MiniLMUnavailableError`; callers must not
    fall back to a remote API.
    """
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return None

    model = _get_model()
    try:
        encoded = model.encode(normalized, normalize_embeddings=True)
    except Exception as exc:  # pragma: no cover - model-dependent failure path
        raise MiniLMUnavailableError(f"MiniLM embedding failed: {exc}") from exc

    vector = np.asarray(encoded, dtype=np.float32).reshape(-1)
    if vector.shape[0] != EMBEDDING_DIM:
        raise MiniLMUnavailableError(
            f"MiniLM returned {vector.shape[0]} dimensions; expected {EMBEDDING_DIM}."
        )
    return [float(value) for value in vector.tolist()]


def _get_model() -> Any:
    global _model, _load_error
    if _model is not None:
        return _model
    if _load_error is not None:
        raise MiniLMUnavailableError(_load_error)

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception as exc:  # pragma: no cover - depends on local model cache
        _load_error = (
            f"Local MiniLM model '{MODEL_NAME}' is unavailable. Install/cache it "
            "locally for embedding generation; no remote API fallback is used. "
            f"Original error: {exc}"
        )
        raise MiniLMUnavailableError(_load_error) from exc
    return _model
