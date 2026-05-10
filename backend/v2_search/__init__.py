"""Runtime helpers for V2 prototype semantic search.

Public surface:
    embed_query(text)            -> list[float]   # 384-dim, L2-normalized
    vector_to_pg_literal(vec)    -> str            # pgvector text format

Why a separate package?
    The hash-based embedder lives in db_v2/scenario/embedder.py — that
    module's scope is "seed/scenario tooling". Importing it directly from
    runtime routers blurs the layer boundary. This package is the runtime
    facade so request handlers depend on `v2_search.*`, not on db_v2 internals.
"""

from .embedder import embed_query
from .pg import vector_to_pg_literal

__all__ = ["embed_query", "vector_to_pg_literal"]
