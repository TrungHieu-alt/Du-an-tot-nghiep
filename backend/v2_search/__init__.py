"""Runtime helpers for V2 prototype semantic search.

Public surface:
    embed_query(text)            -> list[float] | None   # local MiniLM vector
    vector_to_pg_literal(vec)    -> str            # pgvector text format

Why a separate package?
    Request handlers depend on `v2_search.*` instead of importing model
    libraries directly. The runtime embedding implementation is local MiniLM
    only; it has no external AI API fallback.
"""

from .embedder import embed_query
from .pg import vector_to_pg_literal

__all__ = ["embed_query", "vector_to_pg_literal"]
