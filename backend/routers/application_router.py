"""Normal application submission APIs.

This router connects normal Jobs and CVs through PostgreSQL application rows.
It is intentionally separate from Matching V2 and does not calculate scores.
"""

from __future__ import annotations

import math
from typing import Annotated, Any
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from routers.auth import AuthUser, get_current_user, get_db_connection
from schemas.normal_application_schema import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationOut,
    ApplicationUpdateStatus,
)


router = APIRouter(tags=["normal-applications"])

DbConnection = Annotated[psycopg.Connection, Depends(get_db_connection)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

APPLICATION_SELECT_SQL = """
    a.id::text,
    a.job_id::text,
    a.cv_id::text,
    a.candidate_id::text,
    a.recruiter_id::text,
    a.status,
    a.cover_letter,
    a.created_at,
    a.updated_at,
    j.id::text,
    j.title,
    j.company_name,
    c.id::text,
    c.fullname,
    c.headline,
    u.id::text,
    u.email,
    u.full_name,
    u.role
"""


def _pagination(total: int, page: int, limit: int) -> dict[str, int]:
    total_pages = math.ceil(total / limit) if total else 0
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": total_pages,
    }


def _row_to_application(row: tuple[Any, ...]) -> ApplicationOut:
    return ApplicationOut(
        id=row[0],
        jobId=row[1],
        cvId=row[2],
        candidateId=row[3],
        recruiterId=row[4],
        status=row[5],
        coverLetter=row[6],
        createdAt=row[7],
        updatedAt=row[8],
        job={
            "id": row[9],
            "title": row[10],
            "companyName": row[11],
        },
        cv={
            "id": row[12],
            "fullname": row[13],
            "headline": row[14],
        },
        candidate={
            "id": row[15],
            "email": row[16],
            "fullName": row[17],
            "role": row[18],
        },
    )


def _fetch_cv(conn: psycopg.Connection, cv_id: UUID) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, created_by::text, fullname, headline
            FROM cvs
            WHERE id = %s::uuid
            """,
            (str(cv_id),),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "created_by": row[1],
        "fullname": row[2],
        "headline": row[3],
    }


def _fetch_job(conn: psycopg.Connection, job_id: UUID) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, created_by::text, title, company_name, status, visibility, archived
            FROM jobs
            WHERE id = %s::uuid
            """,
            (str(job_id),),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "created_by": row[1],
        "title": row[2],
        "company_name": row[3],
        "status": row[4],
        "visibility": row[5],
        "archived": row[6],
    }


def _is_open_job(job: dict[str, Any]) -> bool:
    return (
        job.get("status") == "published"
        and job.get("visibility") == "public"
        and not job.get("archived")
    )


def _can_manage_job(job: dict[str, Any], user: AuthUser) -> bool:
    return job["created_by"] == user.id or user.role == "admin"


def _fetch_application(conn: psycopg.Connection, application_id: UUID) -> ApplicationOut | None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {APPLICATION_SELECT_SQL}
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            JOIN cvs c ON c.id = a.cv_id
            JOIN users u ON u.id = a.candidate_id
            WHERE a.id = %s::uuid
            """,
            (str(application_id),),
        )
        row = cur.fetchone()
    return _row_to_application(row) if row else None


def _list_applications(
    conn: psycopg.Connection,
    where_sql: str,
    params: tuple[Any, ...],
    page: int,
    limit: int,
) -> ApplicationListResponse:
    offset = (page - 1) * limit
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM applications a
            WHERE {where_sql}
            """,
            params,
        )
        total_row = cur.fetchone()
        total = int(total_row[0]) if total_row else 0
        cur.execute(
            f"""
            SELECT {APPLICATION_SELECT_SQL}
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            JOIN cvs c ON c.id = a.cv_id
            JOIN users u ON u.id = a.candidate_id
            WHERE {where_sql}
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        rows = cur.fetchall()
    pagination = _pagination(total, page, limit)
    return ApplicationListResponse(
        items=[_row_to_application(row) for row in rows],
        total=total,
        page=page,
        limit=limit,
        totalPages=pagination["totalPages"],
        pagination=pagination,
    )


@router.post(
    "/applications",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate,
    conn: DbConnection,
    user: CurrentUser,
) -> ApplicationOut:
    cv = _fetch_cv(conn, payload.cvId)
    if cv is None or cv["created_by"] != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")

    job = _fetch_job(conn, payload.jobId)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not _is_open_job(job):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not open for applications",
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text
                FROM applications
                WHERE candidate_id = %s::uuid
                  AND job_id = %s::uuid
                """,
                (user.id, str(payload.jobId)),
            )
            if cur.fetchone() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Application already exists for this job",
                )
            cur.execute(
                """
                INSERT INTO applications (
                    job_id,
                    cv_id,
                    candidate_id,
                    recruiter_id,
                    status,
                    cover_letter
                )
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, 'submitted', %s)
                RETURNING id::text
                """,
                (
                    str(payload.jobId),
                    str(payload.cvId),
                    user.id,
                    job["created_by"],
                    payload.coverLetter,
                ),
            )
            created = cur.fetchone()
            cur.execute(
                """
                UPDATE jobs
                SET applications_count = applications_count + 1
                WHERE id = %s::uuid
                """,
                (str(payload.jobId),),
            )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists for this job",
        ) from None
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not created:
        raise HTTPException(status_code=500, detail="Application was not created")
    application = _fetch_application(conn, UUID(str(created[0])))
    if application is None:
        raise HTTPException(status_code=500, detail="Application was not created")
    return application


@router.get("/applications/me", response_model=ApplicationListResponse)
def list_my_applications(
    conn: DbConnection,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> ApplicationListResponse:
    return _list_applications(
        conn,
        "a.candidate_id = %s::uuid",
        (user.id,),
        page,
        limit,
    )


@router.get("/job/{job_id}/applications", response_model=ApplicationListResponse)
def list_job_applications(
    job_id: UUID,
    conn: DbConnection,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
) -> ApplicationListResponse:
    job = _fetch_job(conn, job_id)
    if job is None or not _can_manage_job(job, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _list_applications(
        conn,
        "a.job_id = %s::uuid",
        (str(job_id),),
        page,
        limit,
    )


@router.patch("/applications/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: UUID,
    payload: ApplicationUpdateStatus,
    conn: DbConnection,
    user: CurrentUser,
) -> ApplicationOut:
    application = _fetch_application(conn, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job = _fetch_job(conn, application.jobId)
    if job is None or not _can_manage_job(job, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE applications
                SET status = %s
                WHERE id = %s::uuid
                """,
                (payload.status, str(application_id)),
            )
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    updated = _fetch_application(conn, application_id)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return updated
