from __future__ import annotations

from typing import Any, Optional

import psycopg

from jobconnect.modules.api.shared import CurrentUser, Paginated, _dt, business_error, notify, validate_application_transition
from jobconnect.modules.applications.schemas import (
    ApplicationDetail,
    ApplicationEvent,
    ApplicationRequest,
    ApplicationSummary,
    ApplicationStatusRequest,
)
from jobconnect.modules.jobs.service import get_job_row, job_summary
from jobconnect.modules.resumes.service import get_resume_row, resume_summary


APPLICATION_DETAIL_SELECT = """
    a.application_id, a.job_id, a.candidate_user_id, a.resume_id, a.status,
    a.applied_at, a.updated_at, j.recruiter_user_id,
    j.job_id, j.title, j.location, j.job_type, j.seniority, j.education,
    j.skills, j.required_certifications, j.status, j.published_at,
    r.resume_id, r.title, r.location, r.job_type, r.seniority, r.education,
    r.skills, r.certifications, r.status
"""


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def application_detail(row: tuple, events: Optional[list[ApplicationEvent]] = None) -> ApplicationDetail:
    job = job_summary(row[8:18]) if len(row) >= 18 else None
    resume = resume_summary(row[18:27]) if len(row) >= 27 else None
    return ApplicationDetail(
        application_id=row[0],
        job_id=row[1],
        candidate_user_id=row[2],
        resume_id=row[3],
        status=row[4],
        applied_at=_dt(row[5]) if len(row) > 5 else None,
        updated_at=_dt(row[6]) if len(row) > 6 else None,
        job_summary=job,
        resume_summary=resume,
        events=events or [],
    )


def application_summary(row: tuple) -> ApplicationSummary:
    return ApplicationSummary(**application_detail(row).model_dump(exclude={"events"}))


def application_visibility(user: CurrentUser, status: Any, job_id: Any, resume_id: Any):
    if user.role == "candidate":
        where = ["a.candidate_user_id = %s"]
        params: list[Any] = [user.user_id]
    elif user.role == "recruiter":
        where = ["j.recruiter_user_id = %s"]
        params = [user.user_id]
    else:
        where = ["TRUE"]
        params = []
    if status:
        where.append("a.status = %s")
        params.append(status)
    if job_id:
        where.append("a.job_id = %s")
        params.append(job_id)
    if resume_id:
        where.append("a.resume_id = %s")
        params.append(resume_id)
    return " AND ".join(where), params


def get_application_row(application_id: int, user: CurrentUser) -> Optional[tuple]:
    where, params = application_visibility(user, None, None, None)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {APPLICATION_DETAIL_SELECT}
            FROM applications a
            JOIN job_posts j USING (job_id)
            JOIN candidate_resumes r USING (resume_id)
            WHERE {where} AND a.application_id = %s
            """,
            (*params, application_id),
        )
        return cur.fetchone()


def _select_application_by_pair(cur: Any, job_id: int, resume_id: int) -> Optional[tuple]:
    cur.execute(
        f"""
        SELECT {APPLICATION_DETAIL_SELECT}
        FROM applications a
        JOIN job_posts j USING (job_id)
        JOIN candidate_resumes r USING (resume_id)
        WHERE a.job_id = %s AND a.resume_id = %s
        """,
        (job_id, resume_id),
    )
    return cur.fetchone()


def _select_application_by_id(cur: Any, application_id: int) -> Optional[tuple]:
    cur.execute(
        f"""
        SELECT {APPLICATION_DETAIL_SELECT}
        FROM applications a
        JOIN job_posts j USING (job_id)
        JOIN candidate_resumes r USING (resume_id)
        WHERE a.application_id = %s
        """,
        (application_id,),
    )
    return cur.fetchone()


def validate_application_inputs(job_id: int, resume_id: int, candidate_user_id: int) -> tuple[tuple, tuple]:
    resume = get_resume_row(resume_id)
    if resume is None:
        raise business_error(404, "not_found", "Resume not found.")
    if resume[1] != candidate_user_id:
        raise business_error(403, "forbidden", "Candidates can apply only with their own resumes.")
    if resume[12] != "active":
        raise business_error(400, "inactive_resume", "Application requires an active resume.")

    job = get_job_row(job_id)
    if job is None:
        raise business_error(404, "not_found", "Job not found.")
    if job[11] == "closed":
        raise business_error(409, "job_closed", "Closed jobs do not accept applications.")
    if job[11] != "published":
        raise business_error(400, "invalid_job_state", "Application requires a published job.")
    return resume, job


def create_application_in_cursor(
    cur: Any,
    job_id: int,
    resume_id: int,
    candidate_user_id: int,
    actor_user_id: int,
    note: Optional[str],
    recruiter_user_id: int,
    allow_existing: bool = False,
) -> tuple:
    existing = _select_application_by_pair(cur, job_id, resume_id)
    if existing is not None:
        if allow_existing:
            return existing
        raise business_error(409, "duplicate_application", "Application already exists.")

    cur.execute(
        """
        INSERT INTO applications (job_id, candidate_user_id, resume_id)
        VALUES (%s, %s, %s)
        RETURNING application_id
        """,
        (job_id, candidate_user_id, resume_id),
    )
    row = cur.fetchone()
    application_id = row[0]
    cur.execute(
        """
        INSERT INTO application_events
            (application_id, from_status, to_status, actor_user_id, note)
        VALUES (%s, NULL, 'submitted', %s, %s)
        """,
        (application_id, actor_user_id, note),
    )
    notify(
        cur,
        recruiter_user_id,
        "application_submitted",
        "Application submitted",
        "A candidate applied to your job.",
        "application",
        application_id,
        actor_id=actor_user_id,
        metadata={
            "application_id": application_id,
            "job_id": job_id,
            "resume_id": resume_id,
            "candidate_user_id": candidate_user_id,
        },
    )
    from jobconnect.modules.api.shared import audit

    audit(
        cur,
        actor_user_id,
        "candidate_applied",
        "application",
        application_id,
        metadata={
            "job_id": job_id,
            "resume_id": resume_id,
            "candidate_user_id": candidate_user_id,
            "recruiter_user_id": recruiter_user_id,
        },
    )
    created = _select_application_by_id(cur, application_id)
    if created is None:
        raise business_error(500, "application_create_failed", "Application was not readable after creation.")
    return created


def create_application_record(
    job_id: int,
    resume_id: int,
    candidate_user_id: int,
    actor_user_id: int,
    note: Optional[str],
    allow_existing: bool = False,
) -> tuple:
    _resume, job = validate_application_inputs(job_id, resume_id, candidate_user_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        try:
            return create_application_in_cursor(
                cur,
                job_id,
                resume_id,
                candidate_user_id,
                actor_user_id,
                note,
                job[2],
                allow_existing=allow_existing,
            )
        except psycopg.errors.UniqueViolation as exc:
            if not allow_existing:
                raise business_error(409, "duplicate_application", "Application already exists.") from exc
            conn.rollback()
            with conn.cursor() as cur2:
                existing = _select_application_by_pair(cur2, job_id, resume_id)
                if existing is None:
                    raise business_error(409, "duplicate_application", "Application already exists.") from exc
                return existing


def list_applications(
    status: Optional[str],
    job_id: Optional[int],
    resume_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = application_visibility(user, status, job_id, resume_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM applications a JOIN job_posts j USING (job_id) WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT {APPLICATION_DETAIL_SELECT}
            FROM applications a
            JOIN job_posts j USING (job_id)
            JOIN candidate_resumes r USING (resume_id)
            WHERE {where}
            ORDER BY a.application_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [application_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_application(request: ApplicationRequest, user: CurrentUser) -> ApplicationSummary:
    row = create_application_record(request.job_id, request.resume_id, user.user_id, user.user_id, request.note)
    return application_summary(row)


def get_application(application_id: int, user: CurrentUser) -> ApplicationDetail:
    row = get_application_row(application_id, user)
    if row is None:
        raise business_error(404, "not_found", "Application not found.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT event_id, from_status, to_status, actor_user_id, note, created_at
              FROM application_events
             WHERE application_id = %s
             ORDER BY created_at ASC, event_id ASC
            """,
            (application_id,),
        )
        events = [
            ApplicationEvent(
                event_id=r[0],
                from_status=r[1],
                to_status=r[2],
                actor_user_id=r[3],
                note=r[4],
                created_at=_dt(r[5]),
            )
            for r in cur.fetchall()
        ]
    return application_detail(row, events=events)


def update_application_status(application_id: int, request: ApplicationStatusRequest, user: CurrentUser) -> ApplicationDetail:
    row = get_application_row(application_id, user)
    if row is None:
        raise business_error(404, "not_found", "Application not found.")
    current = row[4]
    validate_application_transition(current, request.status, user.role)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE applications SET status = %s, updated_at = now() WHERE application_id = %s RETURNING application_id",
            (request.status, application_id),
        )
        updated = cur.fetchone()
        cur.execute(
            "INSERT INTO application_events (application_id, from_status, to_status, actor_user_id, note) VALUES (%s, %s, %s, %s, %s)",
            (application_id, current, request.status, user.user_id, request.note),
        )
        notify_recipient = row[2]
        if user.role == "candidate" and len(row) > 7:
            notify_recipient = row[7]
        notify(
            cur,
            notify_recipient,
            "application_status_changed",
            "Application status changed",
            f"Application is now {request.status}.",
            "application",
            application_id,
            actor_id=user.user_id,
            metadata={
                "application_id": application_id,
                "from_status": current,
                "to_status": request.status,
                "actor_role": user.role,
                "job_id": row[1],
                "resume_id": row[3],
            },
        )
        from jobconnect.modules.api.shared import audit

        audit(
            cur,
            user.user_id,
            "application_status_changed",
            "application",
            application_id,
            metadata={
                "from_status": current,
                "to_status": request.status,
                "actor_role": user.role,
                "job_id": row[1],
                "resume_id": row[3],
                "recipient_user_id": notify_recipient,
            },
        )
        detail_row = _select_application_by_id(cur, updated[0])
        if detail_row is None:
            raise business_error(500, "application_update_failed", "Application was not readable after status update.")
        cur.execute(
            """
            SELECT event_id, from_status, to_status, actor_user_id, note, created_at
              FROM application_events
             WHERE application_id = %s
             ORDER BY created_at ASC, event_id ASC
            """,
            (application_id,),
        )
        events = [
            ApplicationEvent(
                event_id=r[0],
                from_status=r[1],
                to_status=r[2],
                actor_user_id=r[3],
                note=r[4],
                created_at=_dt(r[5]),
            )
            for r in cur.fetchall()
        ]
    return application_detail(detail_row, events=events)
