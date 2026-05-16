from __future__ import annotations

from typing import Any, Optional

import psycopg

from jobconnect.integrations.pgvector import vector_to_pg_literal
from jobconnect.modules.api.shared import (
    CurrentUser,
    Paginated,
    RESUME_STATUS_TRANSITIONS,
    _list,
    business_error,
    public_resume_filters,
)
from jobconnect.modules.matching.schemas import SemanticSearchRequest
from jobconnect.modules.resumes.schemas import (
    ResumeDetail,
    ResumeRequest,
    ResumeSummary,
    ResumeUpdateRequest,
    SemanticResumeItem,
    SemanticResumeSearchResponse,
)

RESUME_DETAIL_COLS = (
    "resume_id, candidate_user_id, title, summary, experience, skills, location, "
    "job_type, seniority, education, certifications, is_primary, status"
)


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def _dt(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def _vec(text: str) -> str:
    return vector_to_pg_literal(_api().get_embedding_provider().embed(text))


def _upsert_resume_embeddings(conn: psycopg.Connection, resume_id: int, data: ResumeRequest) -> None:
    provider = _api().get_embedding_provider()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_resume_embeddings
                (resume_id, emb_title, emb_skills, emb_summary, emb_experience, embedding_version)
            VALUES (%s, %s::vector, %s::vector, %s::vector, %s::vector, %s)
            ON CONFLICT (resume_id) DO UPDATE SET
                emb_title = EXCLUDED.emb_title,
                emb_skills = EXCLUDED.emb_skills,
                emb_summary = EXCLUDED.emb_summary,
                emb_experience = EXCLUDED.emb_experience,
                embedding_version = EXCLUDED.embedding_version,
                updated_at = now()
            """,
            (
                resume_id,
                vector_to_pg_literal(provider.embed(data.title)),
                vector_to_pg_literal(provider.embed(" ".join(data.skills))),
                vector_to_pg_literal(provider.embed(data.summary)),
                vector_to_pg_literal(provider.embed(data.experience)),
                provider.embedding_version,
            ),
        )


def resume_summary(row: tuple) -> ResumeSummary:
    return ResumeSummary(
        resume_id=row[0],
        title=row[1],
        location=row[2],
        job_type=row[3],
        seniority=row[4],
        education=row[5],
        skills=_list(row[6]),
        certifications=_list(row[7]),
        status=row[8],
    )


def resume_detail(row: tuple) -> ResumeDetail:
    base = resume_summary((row[0], row[2], row[6], row[7], row[8], row[9], row[5], row[10], row[12]))
    return ResumeDetail(
        **base.model_dump(),
        candidate_user_id=row[1],
        summary=row[3],
        experience=row[4],
        is_primary=row[11],
    )


def get_resume_row(resume_id: int) -> Optional[tuple]:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {RESUME_DETAIL_COLS} FROM candidate_resumes WHERE resume_id = %s", (resume_id,))
        return cur.fetchone()


def list_resumes(
    status: Optional[str],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where = ["candidate_user_id = %s"] if user.role == "candidate" else ["TRUE"]
    params: list[Any] = [user.user_id] if user.role == "candidate" else []
    if status:
        where.append("status = %s")
        params.append(status)
    sql_where = " AND ".join(where)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM candidate_resumes WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT resume_id, title, location, job_type, seniority, education, skills, certifications, status
            FROM candidate_resumes WHERE {sql_where}
            ORDER BY resume_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [resume_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_resume(request: ResumeRequest, user: CurrentUser) -> ResumeDetail:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_resumes
                (candidate_user_id, title, summary, experience, skills, location,
                 job_type, seniority, education, certifications, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING """
            + RESUME_DETAIL_COLS,
            (
                user.user_id,
                request.title,
                request.summary,
                request.experience,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.certifications,
                request.is_primary,
            ),
        )
        row = cur.fetchone()
        _upsert_resume_embeddings(conn, row[0], request)
    return resume_detail(row)


def search_resumes(
    q: Optional[str],
    location: Optional[str],
    job_type: Optional[str],
    seniority: Optional[str],
    limit: int,
    offset: int,
) -> Paginated:
    where, params = public_resume_filters(q, location, job_type, seniority)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM candidate_resumes WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT resume_id, title, location, job_type, seniority, education, skills, certifications, status
            FROM candidate_resumes WHERE {where}
            ORDER BY resume_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [resume_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def semantic_search_resumes(request: SemanticSearchRequest) -> SemanticResumeSearchResponse:
    q_vec = _vec(request.query)
    where, params = public_resume_filters(
        None,
        request.filters.get("location"),
        request.filters.get("job_type"),
        request.filters.get("seniority"),
    )
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT r.resume_id, r.title, r.location, r.job_type, r.seniority, r.education,
                   r.skills, r.certifications, r.status,
                   GREATEST(
                       COALESCE(1 - (e.emb_summary <=> %s::vector), -1),
                       COALESCE(1 - (e.emb_experience <=> %s::vector), -1)
                   ) AS relevance_score
            FROM candidate_resumes r
            JOIN candidate_resume_embeddings e USING (resume_id)
            WHERE {where} AND (e.emb_summary IS NOT NULL OR e.emb_experience IS NOT NULL)
            ORDER BY relevance_score DESC, r.resume_id ASC
            LIMIT %s
            """,
            (q_vec, q_vec, *params, request.top_k),
        )
        items = [
            SemanticResumeItem(
                **resume_summary(r[:9]).model_dump(),
                relevance_score=max(0.0, min(1.0, float(r[9]))),
            )
            for r in cur.fetchall()
        ]
    return SemanticResumeSearchResponse(items=items, total=len(items), limit=request.top_k, offset=0)


def get_resume(resume_id: int, user: CurrentUser) -> ResumeDetail:
    row = get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if user.role == "candidate" and row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can read only your own resumes.")
    if user.role == "recruiter" and row[12] != "active":
        raise business_error(404, "not_found", "Resume not found.")
    return resume_detail(row)


def update_resume(resume_id: int, request: ResumeUpdateRequest, user: CurrentUser) -> ResumeDetail:
    row = get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own resumes.")
    patch = request.model_dump(exclude_unset=True)
    if not patch:
        return resume_detail(row)
    set_parts = [f"{col} = %s" for col in patch]
    params: list[Any] = list(patch.values())
    set_parts.append("updated_at = now()")
    params.append(resume_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE candidate_resumes SET {', '.join(set_parts)} WHERE resume_id = %s RETURNING {RESUME_DETAIL_COLS}",
            params,
        )
        updated = cur.fetchone()
        merged = ResumeRequest(
            title=updated[2],
            summary=updated[3] or "",
            experience=updated[4] or "",
            skills=list(updated[5] or []),
            location=updated[6],
            job_type=updated[7],
            seniority=updated[8],
            education=updated[9],
            certifications=list(updated[10] or []),
            is_primary=bool(updated[11]),
        )
        _upsert_resume_embeddings(conn, resume_id, merged)
    return resume_detail(updated)


def _set_resume_status(resume_id: int, status: str, user: CurrentUser) -> ResumeDetail:
    row = get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own resumes.")
    current = row[12]
    allowed_from = RESUME_STATUS_TRANSITIONS.get(status, set())
    if current not in allowed_from:
        raise business_error(409, "invalid_transition", f"Resume cannot transition from {current} to {status}.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE candidate_resumes SET status = %s, updated_at = now() WHERE resume_id = %s RETURNING {RESUME_DETAIL_COLS}",
            (status, resume_id),
        )
        updated = cur.fetchone()
        from jobconnect.modules.api.shared import audit

        audit(cur, user.user_id, f"resume_{status}", "resume", resume_id)
    return resume_detail(updated)


def activate_resume(resume_id: int, user: CurrentUser) -> ResumeDetail:
    return _set_resume_status(resume_id, "active", user)


def archive_resume(resume_id: int, user: CurrentUser) -> ResumeDetail:
    return _set_resume_status(resume_id, "archived", user)
