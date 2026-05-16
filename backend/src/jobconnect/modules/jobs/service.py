from __future__ import annotations

from typing import Any, Optional

import psycopg

from jobconnect.integrations.pgvector import vector_to_pg_literal
from jobconnect.modules.api.shared import (
    CurrentUser,
    JOB_STATUS_TRANSITIONS,
    Paginated,
    _list,
    audit,
    business_error,
    visible_job_search_filter,
)
from jobconnect.modules.jobs.schemas import (
    JobDetail,
    JobRequest,
    JobSummary,
    JobUpdateRequest,
    SemanticJobItem,
    SemanticJobSearchResponse,
)
from jobconnect.modules.matching.schemas import SemanticSearchRequest

JOB_DETAIL_COLS = (
    "job_id, organization_id, recruiter_user_id, title, requirement, skills, "
    "location, job_type, seniority, education, required_certifications, status, "
    "published_at, expires_at"
)


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def _dt(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def _vec(text: str) -> str:
    return vector_to_pg_literal(_api().get_embedding_provider().embed(text))


def _upsert_job_embeddings(conn: psycopg.Connection, job_id: int, data: JobRequest) -> None:
    provider = _api().get_embedding_provider()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO job_post_embeddings
                (job_id, emb_title, emb_skills, emb_requirement, embedding_version)
            VALUES (%s, %s::vector, %s::vector, %s::vector, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                emb_title = EXCLUDED.emb_title,
                emb_skills = EXCLUDED.emb_skills,
                emb_requirement = EXCLUDED.emb_requirement,
                embedding_version = EXCLUDED.embedding_version,
                updated_at = now()
            """,
            (
                job_id,
                vector_to_pg_literal(provider.embed(data.title)),
                vector_to_pg_literal(provider.embed(" ".join(data.skills))),
                vector_to_pg_literal(provider.embed(data.requirement)),
                provider.embedding_version,
            ),
        )


def job_summary(row: tuple) -> JobSummary:
    return JobSummary(
        job_id=row[0],
        title=row[1],
        location=row[2],
        job_type=row[3],
        seniority=row[4],
        education=row[5],
        skills=_list(row[6]),
        required_certifications=_list(row[7]),
        status=row[8],
        published_at=_dt(row[9]),
    )


def job_detail(row: tuple) -> JobDetail:
    base = job_summary((row[0], row[3], row[6], row[7], row[8], row[9], row[5], row[10], row[11], row[12]))
    return JobDetail(
        **base.model_dump(),
        organization_id=row[1],
        recruiter_user_id=row[2],
        requirement=row[4],
        expires_at=_dt(row[13]),
    )


def get_job_row(job_id: int) -> Optional[tuple]:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {JOB_DETAIL_COLS} FROM job_posts WHERE job_id = %s", (job_id,))
        return cur.fetchone()


def list_jobs(
    status: Optional[str],
    location: Optional[str],
    job_type: Optional[str],
    seniority: Optional[str],
    q: Optional[str],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = visible_job_search_filter(user, q, location, job_type, seniority, status)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM job_posts WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT job_id, title, location, job_type, seniority, education, skills,
                   required_certifications, status, published_at
            FROM job_posts WHERE {where}
            ORDER BY job_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [job_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_job(request: JobRequest, user: CurrentUser) -> JobDetail:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM organizations WHERE organization_id = %s", (request.organization_id,))
        if cur.fetchone() is None:
            raise business_error(404, "not_found", "Organization not found.")
        cur.execute(
            """
            INSERT INTO job_posts
                (organization_id, recruiter_user_id, title, requirement, skills, location,
                 job_type, seniority, education, required_certifications, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING """
            + JOB_DETAIL_COLS,
            (
                request.organization_id,
                user.user_id,
                request.title,
                request.requirement,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.required_certifications,
                request.expires_at,
            ),
        )
        row = cur.fetchone()
        _upsert_job_embeddings(conn, row[0], request)
    return job_detail(row)


def search_jobs(
    q: Optional[str],
    location: Optional[str],
    job_type: Optional[str],
    seniority: Optional[str],
    status: Optional[str],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = visible_job_search_filter(user, None, location, job_type, seniority, status)
    if q:
        pat = f"%{q}%"
        where = (
            f"{where} AND (title ILIKE %s OR array_to_string(skills, ' ') ILIKE %s "
            "OR organization_id IN (SELECT organization_id FROM organizations WHERE name ILIKE %s))"
        )
        params.extend([pat, pat, pat])
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM job_posts WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT job_id, title, location, job_type, seniority, education, skills,
                   required_certifications, status, published_at
            FROM job_posts WHERE {where}
            ORDER BY job_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [job_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def semantic_search_jobs(request: SemanticSearchRequest, user: CurrentUser) -> SemanticJobSearchResponse:
    q_vec = _vec(request.query)
    where, params = visible_job_search_filter(
        user,
        None,
        request.filters.get("location"),
        request.filters.get("job_type"),
        request.filters.get("seniority"),
        None,
    )
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT j.job_id, j.title, j.location, j.job_type, j.seniority, j.education,
                   j.skills, j.required_certifications, j.status, j.published_at,
                   1 - (e.emb_requirement <=> %s::vector) AS relevance_score
            FROM job_posts j
            JOIN job_post_embeddings e USING (job_id)
            WHERE {where} AND e.emb_requirement IS NOT NULL
            ORDER BY relevance_score DESC, j.job_id ASC
            LIMIT %s
            """,
            (q_vec, *params, request.top_k),
        )
        items = [
            SemanticJobItem(
                **job_summary(r[:10]).model_dump(),
                relevance_score=max(0.0, min(1.0, float(r[10]))),
            )
            for r in cur.fetchall()
        ]
    return SemanticJobSearchResponse(items=items, total=len(items), limit=request.top_k, offset=0)


def get_job(job_id: int, user: CurrentUser) -> JobDetail:
    row = get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "candidate" and row[11] != "published":
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can read only your own unpublished jobs.")
    return job_detail(row)


def update_job(job_id: int, request: JobUpdateRequest, user: CurrentUser) -> JobDetail:
    row = get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own jobs.")
    patch = request.model_dump(exclude_unset=True)
    if not patch:
        return job_detail(row)
    set_parts = [f"{col} = %s" for col in patch]
    params: list[Any] = list(patch.values())
    set_parts.append("updated_at = now()")
    params.append(job_id)

    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE job_posts SET {', '.join(set_parts)} WHERE job_id = %s RETURNING {JOB_DETAIL_COLS}",
            params,
        )
        updated = cur.fetchone()
        merged = JobRequest(
            organization_id=updated[1],
            title=updated[3],
            requirement=updated[4] or "",
            skills=list(updated[5] or []),
            location=updated[6],
            job_type=updated[7],
            seniority=updated[8],
            education=updated[9],
            required_certifications=list(updated[10] or []),
            expires_at=_dt(updated[13]),
        )
        _upsert_job_embeddings(conn, job_id, merged)
    return job_detail(updated)


def _set_job_status(job_id: int, status: str, user: CurrentUser) -> JobDetail:
    row = get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own jobs.")
    current = row[11]
    allowed_from = JOB_STATUS_TRANSITIONS.get(status, set())
    if current not in allowed_from:
        raise business_error(409, "invalid_transition", f"Job cannot transition from {current} to {status}.")
    published_set = ", published_at = COALESCE(published_at, now())" if status == "published" else ""
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE job_posts SET status = %s{published_set}, updated_at = now() WHERE job_id = %s RETURNING {JOB_DETAIL_COLS}",
            (status, job_id),
        )
        updated = cur.fetchone()
        audit(cur, user.user_id, f"job_{status}", "job", job_id)
    return job_detail(updated)


def publish_job(job_id: int, user: CurrentUser) -> JobDetail:
    return _set_job_status(job_id, "published", user)


def close_job(job_id: int, user: CurrentUser) -> JobDetail:
    return _set_job_status(job_id, "closed", user)
