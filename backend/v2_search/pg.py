"""pgvector text-literal helpers.

pgvector accepts vectors as strings of the form '[0.1,0.2,0.3]' which
can be cast to ::vector inside SQL. This avoids a hard dependency on
the optional pgvector psycopg adapter — matching the approach already
used by backend/matching_v2/db.py to read vectors via ::text.
"""

from __future__ import annotations

from typing import Iterable


def vector_to_pg_literal(vec: Iterable[float]) -> str:
    """Render a numeric iterable as a pgvector text literal.

    Output format: '[x1,x2,...]' — no spaces, exactly what pgvector
    expects when the column type is `vector(N)`. Caller is responsible
    for binding via parameter (e.g. `'%s::vector'`) so SQL injection is
    not a concern, but we still emit a strict format to be safe.

    Args:
        vec: Iterable of floats (or values castable to float).

    Returns:
        A string like '[0.1,0.2,0.3]'.

    Examples:
        >>> vector_to_pg_literal([0.1, 0.2])
        '[0.1,0.2]'
        >>> vector_to_pg_literal([])
        '[]'
    """
    body = ",".join(repr(float(x)) for x in vec)
    return f"[{body}]"
