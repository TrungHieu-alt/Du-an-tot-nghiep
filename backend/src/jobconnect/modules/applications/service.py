from __future__ import annotations

from typing import Any, Optional

import psycopg

from jobconnect.modules.api.shared import CurrentUser, Paginated, _dt, business_error, dispatch_email, notify, validate_application_transition
from jobconnect.modules.applications.schemas import (
    ApplicationDetail,
    ApplicationEvent,
    ApplicationRequest,
    ApplicationStatusRequest,
)
from jobconnect.modules.jobs.service import get_job_row
from jobconnect.modules.resumes.service import get_resume_row


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def application_detail(row: tuple) -> ApplicationDetail:
    return ApplicationDetail(
        application_id=row[0],
        job_id=row[1],
        candidate_user_id=row[2],
        resume_id=row[3],
        status=row[4],
    )


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
            SELECT a.application_id, a.job_id, a.candidate_user_id, a.resume_id, a.status
            FROM applications a JOIN job_posts j USING (job_id)
            WHERE {where} AND a.application_id = %s
            """,
            (*params, application_id),
        )
        return cur.fetchone()


def create_application_record(
    job_id: int,
    resume_id: int,
    candidate_user_id: int,
    actor_user_id: int,
    note: Optional[str],
    allow_existing: bool = False,
) -> tuple:
    resume = get_resume_row(resume_id)
    job = get_job_row(job_id)
    if resume is None or resume[12] != "active" or resume[1] != candidate_user_id:
        raise business_error(404, "not_found", "Active owned resume not found.")
    # Slice 9: distinguish closed jobs (409 closed_job) from missing/draft (404 not_found)
    # per REQUIREMENTS §6.3 ("Closed jobs must not accept new applications").
    if job is None:
        raise business_error(404, "not_found", "Published job not found.")
    if job[11] == "closed":
        raise business_error(409, "closed_job", "Job is closed and cannot accept new applications.")
    if job[11] != "published":
        raise business_error(404, "not_found", "Published job not found.")
    notif_id = -1
    with _api().get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO applications (job_id, candidate_user_id, resume_id)
                VALUES (%s, %s, %s)
                RETURNING application_id, job_id, candidate_user_id, resume_id, status
                """,
                (job_id, candidate_user_id, resume_id),
            )
            row = cur.fetchone()
            cur.execute(
                "INSERT INTO application_events (application_id, from_status, to_status, actor_user_id, note) VALUES (%s, NULL, 'submitted', %s, %s)",
                (row[0], actor_user_id, note),
            )
            notif_id = notify(cur, job[2], "application_submitted", "Application submitted", "A candidate applied to your job.", "application", row[0])
            from jobconnect.modules.api.shared import audit

            audit(cur, actor_user_id, "candidate_applied", "application", row[0])
            result_row = row
        except psycopg.errors.UniqueViolation as exc:
            if not allow_existing:
                raise business_error(409, "duplicate_application", "Application already exists.") from exc
            conn.rollback()
            with conn.cursor() as cur2:
                cur2.execute(
                    "SELECT application_id, job_id, candidate_user_id, resume_id, status FROM applications WHERE job_id = %s AND resume_id = %s",
                    (job_id, resume_id),
                )
                result_row = cur2.fetchone()
    if notif_id != -1:
        dispatch_email(notif_id)
    return result_row


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
            SELECT a.application_id, a.job_id, a.candidate_user_id, a.resume_id, a.status
            FROM applications a JOIN job_posts j USING (job_id)
            WHERE {where}
            ORDER BY a.application_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [application_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_application(request: ApplicationRequest, user: CurrentUser) -> ApplicationDetail:
    row = create_application_record(request.job_id, request.resume_id, user.user_id, user.user_id, request.note)
    return application_detail(row)


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
             ORDER BY event_id ASC
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
    detail = application_detail(row)
    return detail.model_copy(update={"events": events})


def update_application_status(application_id: int, request: ApplicationStatusRequest, user: CurrentUser) -> ApplicationDetail:
    row = get_application_row(application_id, user)
    if row is None:
        raise business_error(404, "not_found", "Application not found.")
    current = row[4]
    validate_application_transition(current, request.status, user.role)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE applications SET status = %s, updated_at = now() WHERE application_id = %s RETURNING application_id, job_id, candidate_user_id, resume_id, status",
            (request.status, application_id),
        )
        updated = cur.fetchone()
        cur.execute(
            "INSERT INTO application_events (application_id, from_status, to_status, actor_user_id, note) VALUES (%s, %s, %s, %s, %s)",
            (application_id, current, request.status, user.user_id, request.note),
        )
        notif_id = notify(
            cur,
            updated[2],
            "application_status_changed",
            "Application status changed",
            f"Application is now {request.status}.",
            "application",
            application_id,
        )
        from jobconnect.modules.api.shared import audit

        audit(cur, user.user_id, "application_status_changed", "application", application_id)
    dispatch_email(notif_id)
    return application_detail(updated)
