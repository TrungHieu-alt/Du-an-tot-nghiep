"""PostgreSQL data loaders for the Matching V2 run-only prototype.

All operations are SELECT-only — no writes, no match_results_v2.
Vector columns are cast to ::text in SQL and parsed in Python to avoid
a dependency on the pgvector Python adapter.

Connection defaults: POSTGRES_HOST=localhost, POSTGRES_PORT=5433,
                     POSTGRES_USER=jobmatcher, POSTGRES_PASSWORD=jobmatcher,
                     POSTGRES_DB=jobmatcher_v2.
"""

from __future__ import annotations

import os
from typing import Optional

import psycopg

from .models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_conninfo() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5433')} "
        f"user={os.getenv('POSTGRES_USER', 'jobmatcher')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'jobmatcher')} "
        f"dbname={os.getenv('POSTGRES_DB', 'jobmatcher_v2')}"
    )


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_conninfo())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_vec(s: Optional[str]) -> Optional[list[float]]:
    """Parse pgvector text representation '[0.1,0.2,...]' into list[float]."""
    if s is None:
        return None
    stripped = s.strip()
    if not stripped or stripped == "[]":
        return None
    return [float(x) for x in stripped.strip("[]").split(",")]


def _to_tuple(pg_array: Optional[list]) -> tuple:
    if pg_array is None:
        return ()
    return tuple(pg_array)


# ---------------------------------------------------------------------------
# Job loaders
# ---------------------------------------------------------------------------

_JOB_COLS = (
    "job_id, title, skills, requirement, location, "
    "job_type, seniority, education, required_certifications"
)


def _row_to_job(row: tuple) -> JobPostV2:
    return JobPostV2(
        job_id=row[0],
        title=row[1],
        skills=_to_tuple(row[2]),
        requirement=row[3],
        location=row[4],
        job_type=row[5],
        seniority=row[6],
        education=row[7],
        required_certifications=_to_tuple(row[8]),
    )


def load_job(conn: psycopg.Connection, job_id: int) -> Optional[JobPostV2]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_JOB_COLS} FROM job_posts_v2 WHERE job_id = %s",
            (job_id,),
        )
        row = cur.fetchone()
    return _row_to_job(row) if row else None


def load_all_jobs(conn: psycopg.Connection) -> list[JobPostV2]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {_JOB_COLS} FROM job_posts_v2 ORDER BY job_id ASC")
        rows = cur.fetchall()
    return [_row_to_job(r) for r in rows]


# ---------------------------------------------------------------------------
# Candidate loaders
# ---------------------------------------------------------------------------

_CV_COLS = (
    "cv_id, title, skills, summary, experience, "
    "location, job_type, seniority, education, certifications"
)


def _row_to_cv(row: tuple) -> CandidateProfileV2:
    return CandidateProfileV2(
        cv_id=row[0],
        title=row[1],
        skills=_to_tuple(row[2]),
        summary=row[3],
        experience=row[4],
        location=row[5],
        job_type=row[6],
        seniority=row[7],
        education=row[8],
        certifications=_to_tuple(row[9]),
    )


def load_candidate(conn: psycopg.Connection, cv_id: int) -> Optional[CandidateProfileV2]:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_CV_COLS} FROM candidate_profiles_v2 WHERE cv_id = %s",
            (cv_id,),
        )
        row = cur.fetchone()
    return _row_to_cv(row) if row else None


def load_all_candidates(conn: psycopg.Connection) -> list[CandidateProfileV2]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {_CV_COLS} FROM candidate_profiles_v2 ORDER BY cv_id ASC")
        rows = cur.fetchall()
    return [_row_to_cv(r) for r in rows]


# ---------------------------------------------------------------------------
# Embedding loaders (vector columns cast to ::text)
# ---------------------------------------------------------------------------

def load_job_embeddings(
    conn: psycopg.Connection, job_id: int
) -> Optional[JobEmbeddingsV2]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT job_id,
                   emb_title::text,
                   emb_skills::text,
                   emb_requirement::text
            FROM job_embeddings_v2
            WHERE job_id = %s
            """,
            (job_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return JobEmbeddingsV2(
        job_id=row[0],
        emb_title=_parse_vec(row[1]),
        emb_skills=_parse_vec(row[2]),
        emb_requirement=_parse_vec(row[3]),
    )


def load_all_candidate_embeddings(
    conn: psycopg.Connection,
) -> dict[int, CandidateEmbeddingsV2]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cv_id,
                   emb_title::text,
                   emb_skills::text,
                   emb_summary::text,
                   emb_experience::text
            FROM candidate_embeddings_v2
            ORDER BY cv_id ASC
            """
        )
        rows = cur.fetchall()
    result: dict[int, CandidateEmbeddingsV2] = {}
    for row in rows:
        emb = CandidateEmbeddingsV2(
            cv_id=row[0],
            emb_title=_parse_vec(row[1]),
            emb_skills=_parse_vec(row[2]),
            emb_summary=_parse_vec(row[3]),
            emb_experience=_parse_vec(row[4]),
        )
        result[emb.cv_id] = emb
    return result


def load_candidate_embeddings(
    conn: psycopg.Connection, cv_id: int
) -> Optional[CandidateEmbeddingsV2]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cv_id,
                   emb_title::text,
                   emb_skills::text,
                   emb_summary::text,
                   emb_experience::text
            FROM candidate_embeddings_v2
            WHERE cv_id = %s
            """,
            (cv_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return CandidateEmbeddingsV2(
        cv_id=row[0],
        emb_title=_parse_vec(row[1]),
        emb_skills=_parse_vec(row[2]),
        emb_summary=_parse_vec(row[3]),
        emb_experience=_parse_vec(row[4]),
    )


def load_all_job_embeddings(
    conn: psycopg.Connection,
) -> dict[int, JobEmbeddingsV2]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT job_id,
                   emb_title::text,
                   emb_skills::text,
                   emb_requirement::text
            FROM job_embeddings_v2
            ORDER BY job_id ASC
            """
        )
        rows = cur.fetchall()
    result: dict[int, JobEmbeddingsV2] = {}
    for row in rows:
        emb = JobEmbeddingsV2(
            job_id=row[0],
            emb_title=_parse_vec(row[1]),
            emb_skills=_parse_vec(row[2]),
            emb_requirement=_parse_vec(row[3]),
        )
        result[emb.job_id] = emb
    return result
