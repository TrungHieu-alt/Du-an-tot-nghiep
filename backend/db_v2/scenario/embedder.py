"""Deterministic bag-of-words text embedder for Slice 6B scenario dataset.

Produces 384-dim normalized float32 vectors with no network calls.
Each token is hashed via SHA-256 to seed a reproducible unit vector;
the final embedding is the L2-normalized sum of per-token vectors.

Token deduplication preserves first-occurrence order, matching how
tie-pair CVs (3032/3033) are engineered to produce identical vectors
for titles that share the same token set in different word order.
"""

from __future__ import annotations

import hashlib

import numpy as np


def _token_vector(token: str, dim: int = 384) -> np.ndarray:
    seed_int = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed_int)
    v = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 1e-8 else v


def embed_text(text: str, dim: int = 384) -> np.ndarray:
    """Embed text into a normalized 384-dim float32 vector.

    Tokenizes by whitespace, lowercases, deduplicates preserving order,
    drops single-char tokens. Returns zero vector for empty input.
    """
    tokens = list(dict.fromkeys(text.lower().split()))
    tokens = [t for t in tokens if len(t) > 1]
    if not tokens:
        return np.zeros(dim, dtype=np.float32)
    vec = sum(_token_vector(t, dim) for t in tokens)
    norm = np.linalg.norm(vec)
    return (vec / norm).astype(np.float32) if norm > 1e-8 else vec.astype(np.float32)
