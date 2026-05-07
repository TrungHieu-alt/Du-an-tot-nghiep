"""matching_v2 — run-only Matching V2 prototype package.

Public surface:
    run_for_job(conn, job_id, top_k, min_score) -> RunMatchingV2Response
    run_for_cv(conn, cv_id, top_k, min_score)   -> RunMatchingV2Response
    get_connection()                             -> psycopg.Connection
"""

from .db import get_connection
from .models import MatchItemV2, RunMatchingV2Response
from .runner import run_for_cv, run_for_job

__all__ = [
    "get_connection",
    "run_for_job",
    "run_for_cv",
    "RunMatchingV2Response",
    "MatchItemV2",
]
