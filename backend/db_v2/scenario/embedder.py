"""Scenario text embedder.

Default behavior uses local MiniLM
(`sentence-transformers/all-MiniLM-L6-v2`) through `v2_search.minilm`.
Set `DB_V2_USE_DETERMINISTIC_FIXTURE_EMBEDDINGS=1` only for historical
scenario fixture validation.
"""

from __future__ import annotations

import hashlib
import os

import numpy as np

from v2_search.minilm import EMBEDDING_DIM, embed_text_minilm


FIXTURE_EMBEDDINGS_ENV = "DB_V2_USE_DETERMINISTIC_FIXTURE_EMBEDDINGS"


def _token_vector(token: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    seed_int = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed_int)
    v = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 1e-8 else v


def embed_text(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Embed text into a normalized 384-dim float32 vector.

    Uses local MiniLM by default. The deterministic fixture mode preserves old
    scenario test behavior when explicitly enabled by env var.
    """
    if os.getenv(FIXTURE_EMBEDDINGS_ENV) != "1":
        vector = embed_text_minilm(text)
        if vector is None:
            return np.zeros(dim, dtype=np.float32)
        return np.asarray(vector, dtype=np.float32)

    tokens = list(dict.fromkeys(text.lower().split()))
    tokens = [t for t in tokens if len(t) > 1]
    if not tokens:
        return np.zeros(dim, dtype=np.float32)
    vec = sum(_token_vector(t, dim) for t in tokens)
    norm = np.linalg.norm(vec)
    return (vec / norm).astype(np.float32) if norm > 1e-8 else vec.astype(np.float32)
