"""Runtime embedder facade for V2 search endpoints.

Uses only the local MiniLM model:
`sentence-transformers/all-MiniLM-L6-v2`.

No external AI, hosted embedding, or remote LLM API is used.
"""

from __future__ import annotations

from .minilm import EMBEDDING_DIM, MiniLMUnavailableError, embed_text_minilm


def embed_query(text: str) -> list[float] | None:
    """Embed a search query into a local MiniLM 384-dim list[float].

    Args:
        text: Free-form user query. Empty/whitespace-only input returns None
              and must not be embedded.

    Returns:
        A 384-element normalized list of floats, or None for empty input.

    Raises:
        MiniLMUnavailableError: if the local model files are unavailable.
    """
    vector = embed_text_minilm(text)
    if vector is not None and len(vector) != EMBEDDING_DIM:
        raise MiniLMUnavailableError(
            f"MiniLM returned {len(vector)} dimensions; expected {EMBEDDING_DIM}."
        )
    return vector
