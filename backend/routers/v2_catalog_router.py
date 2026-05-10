"""Read-only catalog endpoints for V2 prototype tables (job_posts_v2, candidate_profiles_v2).

These endpoints exist so the frontend can pick an anchor before invoking the
matching_v2 run endpoints. They are intentionally minimal:
  * SELECT-only — no writes, no LLM, no embeddings.
  * psycopg directly — does NOT touch SQLAlchemy ORM at runtime, preserving
    the scope-lock established by backend/matching_v2/.
  * Connection helper is reused from matching_v2.db.get_connection.

Endpoints (prefix /v2/prototype/catalog):
    GET  /jobs?limit=&offset=
    GET  /jobs/{job_id}
    GET  /cvs?limit=&offset=
    GET  /cvs/{cv_id}
"""

from __future__ import annotations

from typing import Optional  # noqa: F401  (used in type hints + helper signature)

import psycopg
from fastapi import APIRouter, Body, HTTPException, Query

from matching_v2 import get_connection
from schemas.v2_catalog_schema import (
    CatalogErrorResponse,
    CatalogSearchRequest,
    CVSearchItem,
    CVSearchResponse,
    CVV2Detail,
    CVV2ListItem,
    CVV2ListResponse,
    JobSearchItem,
    JobSearchResponse,
    JobV2Detail,
    JobV2ListItem,
    JobV2ListResponse,
)
from v2_search import embed_query, vector_to_pg_literal


router = APIRouter(prefix="/v2/prototype/catalog", tags=["catalog-v2-prototype"])


# ---------------------------------------------------------------------------
# Column constants (mirror matching_v2/db.py for consistency)
# ---------------------------------------------------------------------------

_JOB_LIST_COLS = "job_id, title, location, job_type, seniority, skills"
_JOB_DETAIL_COLS = (
    "job_id, title, skills, requirement, location, "
    "job_type, seniority, education, required_certifications"
)
_CV_LIST_COLS = "cv_id, title, location, job_type, seniority, skills"
_CV_DETAIL_COLS = (
    "cv_id, title, skills, summary, experience, "
    "location, job_type, seniority, education, certifications"
)


def _as_list(pg_array: Optional[list]) -> list[str]:
    return list(pg_array) if pg_array is not None else []


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@router.get(
    "/jobs",
    response_model=JobV2ListResponse,
)
def list_jobs_v2(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> JobV2ListResponse:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM job_posts_v2")
            total_row = cur.fetchone()
            total = int(total_row[0]) if total_row else 0

            cur.execute(
                f"SELECT {_JOB_LIST_COLS} "
                "FROM job_posts_v2 "
                "ORDER BY job_id ASC "
                "LIMIT %s OFFSET %s",
                (limit, offset),
            )
            rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    items = [
        JobV2ListItem(
            job_id=row[0],
            title=row[1],
            location=row[2],
            job_type=row[3],
            seniority=row[4],
            skills=_as_list(row[5]),
        )
        for row in rows
    ]
    return JobV2ListResponse(items=items, total=total)


@router.get(
    "/jobs/{job_id}",
    response_model=JobV2Detail,
    responses={404: {"model": CatalogErrorResponse}},
)
def get_job_v2(job_id: int) -> JobV2Detail:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_JOB_DETAIL_COLS} FROM job_posts_v2 WHERE job_id = %s",
                (job_id,),
            )
            row = cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="job not found")

    return JobV2Detail(
        job_id=row[0],
        title=row[1],
        skills=_as_list(row[2]),
        requirement=row[3],
        location=row[4],
        job_type=row[5],
        seniority=row[6],
        education=row[7],
        required_certifications=_as_list(row[8]),
    )


# ---------------------------------------------------------------------------
# CVs
# ---------------------------------------------------------------------------

@router.get(
    "/cvs",
    response_model=CVV2ListResponse,
)
def list_cvs_v2(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CVV2ListResponse:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM candidate_profiles_v2")
            total_row = cur.fetchone()
            total = int(total_row[0]) if total_row else 0

            cur.execute(
                f"SELECT {_CV_LIST_COLS} "
                "FROM candidate_profiles_v2 "
                "ORDER BY cv_id ASC "
                "LIMIT %s OFFSET %s",
                (limit, offset),
            )
            rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    items = [
        CVV2ListItem(
            cv_id=row[0],
            title=row[1],
            location=row[2],
            job_type=row[3],
            seniority=row[4],
            skills=_as_list(row[5]),
        )
        for row in rows
    ]
    return CVV2ListResponse(items=items, total=total)


@router.get(
    "/cvs/{cv_id}",
    response_model=CVV2Detail,
    responses={404: {"model": CatalogErrorResponse}},
)
def get_cv_v2(cv_id: int) -> CVV2Detail:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_CV_DETAIL_COLS} FROM candidate_profiles_v2 WHERE cv_id = %s",
                (cv_id,),
            )
            row = cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="cv not found")

    return CVV2Detail(
        cv_id=row[0],
        title=row[1],
        skills=_as_list(row[2]),
        summary=row[3],
        experience=row[4],
        location=row[5],
        job_type=row[6],
        seniority=row[7],
        education=row[8],
        certifications=_as_list(row[9]),
    )


# ---------------------------------------------------------------------------
# Semantic search (pgvector cosine, blended title + skills)
# ---------------------------------------------------------------------------
#
# Query plan (jobs; cvs is symmetric):
#   1. Embed `q` once via v2_search.embed_query (deterministic hash-based).
#   2. JOIN job_posts_v2 with job_embeddings_v2 on job_id; require
#      emb_title IS NOT NULL so cosine is well-defined.
#   3. Compute sim_title = 1 - (emb_title <=> q_vec).
#      Compute sim_skills = 1 - (emb_skills <=> q_vec) when present, else 0.
#   4. Score = (1 - blend) * sim_title + blend * sim_skills.
#   5. ORDER BY score DESC, tie-break by id ASC for determinism. LIMIT top_k.
#
# `score` is clamped to [0,1] in Python — pgvector cosine distance lives in
# [0,2], so similarity = 1 - dist lives in [-1,1]. With L2-normalized
# vectors and a non-negative blend, the score stays in [-1,1]; we clamp the
# small negative tail to 0 for a clean UI percentage.

_JOB_SEARCH_SQL_TEMPLATE = """
WITH ranked AS (
    SELECT j.job_id,
           j.title,
           j.location,
           j.job_type,
           j.seniority,
           j.skills,
           1 - (e.emb_title <=> %s::vector) AS sim_title,
           CASE WHEN e.emb_skills IS NULL THEN 0.0
                ELSE 1 - (e.emb_skills <=> %s::vector)
           END AS sim_skills
    FROM job_posts_v2 j
    JOIN job_embeddings_v2 e USING (job_id)
    WHERE e.emb_title IS NOT NULL
    {extra_where}
)
SELECT job_id, title, location, job_type, seniority, skills,
       (1 - %s) * sim_title + %s * sim_skills AS score
FROM ranked
ORDER BY score DESC, job_id ASC
LIMIT %s
"""

_CV_SEARCH_SQL_TEMPLATE = """
WITH ranked AS (
    SELECT c.cv_id,
           c.title,
           c.location,
           c.job_type,
           c.seniority,
           c.skills,
           1 - (e.emb_title <=> %s::vector) AS sim_title,
           CASE WHEN e.emb_skills IS NULL THEN 0.0
                ELSE 1 - (e.emb_skills <=> %s::vector)
           END AS sim_skills
    FROM candidate_profiles_v2 c
    JOIN candidate_embeddings_v2 e USING (cv_id)
    WHERE e.emb_title IS NOT NULL
    {extra_where}
)
SELECT cv_id, title, location, job_type, seniority, skills,
       (1 - %s) * sim_title + %s * sim_skills AS score
FROM ranked
ORDER BY score DESC, cv_id ASC
LIMIT %s
"""


def _build_filter_clause(
    alias: str,
    location: Optional[str],
    job_type: Optional[str],
    seniority: Optional[str],
) -> tuple[str, list[str]]:
    """Build dynamic WHERE additions for catalog search filters.

    Only `%s` placeholders are emitted — user input is never interpolated
    into the SQL string. Values are returned in the same positional order
    as the placeholders so the caller can splice them into the params tuple.

    Args:
        alias: Table alias used in the SELECT (`j` for jobs, `c` for cvs).
        location, job_type, seniority: Optional enum values already validated
            by Pydantic Literal at the schema layer.

    Returns:
        (extra_where, values): the SQL fragment (may be empty string) and
        the corresponding list of bind values, in placeholder order.
    """
    parts: list[str] = []
    values: list[str] = []
    if location is not None:
        parts.append(f"AND {alias}.location = %s")
        values.append(location)
    if job_type is not None:
        parts.append(f"AND {alias}.job_type = %s")
        values.append(job_type)
    if seniority is not None:
        parts.append(f"AND {alias}.seniority = %s")
        values.append(seniority)
    return (" ".join(parts), values)


def _clamp_score(s: float) -> float:
    if s < 0.0:
        return 0.0
    if s > 1.0:
        return 1.0
    return s


@router.post(
    "/jobs/search",
    response_model=JobSearchResponse,
)
def search_jobs_v2(
    request: CatalogSearchRequest = Body(...),
) -> JobSearchResponse:
    q = request.q.strip()
    if not q:
        # Trimmed-empty query: skip DB roundtrip entirely.
        return JobSearchResponse(items=[], total=0)

    q_vec = vector_to_pg_literal(embed_query(q))
    blend = request.blend_skills
    top_k = request.top_k

    extra_where, filter_values = _build_filter_clause(
        alias="j",
        location=request.location,
        job_type=request.job_type,
        seniority=request.seniority,
    )
    sql = _JOB_SEARCH_SQL_TEMPLATE.format(extra_where=extra_where)
    params: tuple = (q_vec, q_vec, *filter_values, blend, blend, top_k)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    items = [
        JobSearchItem(
            job_id=row[0],
            title=row[1],
            location=row[2],
            job_type=row[3],
            seniority=row[4],
            skills=_as_list(row[5]),
            score=_clamp_score(float(row[6])),
        )
        for row in rows
    ]
    return JobSearchResponse(items=items, total=len(items))


@router.post(
    "/cvs/search",
    response_model=CVSearchResponse,
)
def search_cvs_v2(
    request: CatalogSearchRequest = Body(...),
) -> CVSearchResponse:
    q = request.q.strip()
    if not q:
        return CVSearchResponse(items=[], total=0)

    q_vec = vector_to_pg_literal(embed_query(q))
    blend = request.blend_skills
    top_k = request.top_k

    extra_where, filter_values = _build_filter_clause(
        alias="c",
        location=request.location,
        job_type=request.job_type,
        seniority=request.seniority,
    )
    sql = _CV_SEARCH_SQL_TEMPLATE.format(extra_where=extra_where)
    params: tuple = (q_vec, q_vec, *filter_values, blend, blend, top_k)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        conn.close()

    items = [
        CVSearchItem(
            cv_id=row[0],
            title=row[1],
            location=row[2],
            job_type=row[3],
            seniority=row[4],
            skills=_as_list(row[5]),
            score=_clamp_score(float(row[6])),
        )
        for row in rows
    ]
    return CVSearchResponse(items=items, total=len(items))
