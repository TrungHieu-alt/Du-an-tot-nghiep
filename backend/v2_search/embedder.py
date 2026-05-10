"""Runtime embedder facade for V2 search endpoints.

Delegates to the deterministic hash-based embedder used to seed
job_embeddings_v2 and candidate_embeddings_v2 — guaranteeing query
vectors are cosine-comparable with stored embeddings.

The underlying implementation is pure numpy + SHA-256: no model
download, no GPU, no network call, no cold-start cost.
"""

from __future__ import annotations

from db_v2.scenario.embedder import embed_text

_DIM = 384


def embed_query(text: str) -> list[float]:
    """Embed a search query into a 384-dim list[float].

    Args:
        text: Free-form user query. Whitespace-tokenized, lowercased,
              deduplicated preserving first-occurrence order. Tokens of
              length <= 1 are dropped. Empty input returns a zero vector.

    Returns:
        A 384-element list of float (L2-normalized, except zero vector
        for empty input). Plain Python list so it serializes cleanly to
        the pgvector text literal in pg.py.
    """
    return embed_text(text, dim=_DIM).tolist()
