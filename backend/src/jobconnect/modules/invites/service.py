from __future__ import annotations

from typing import Any, Optional

from jobconnect.modules.api.shared import CurrentUser, Paginated, _dt, business_error, notify
from jobconnect.modules.applications.service import (
    application_detail,
    create_application_in_cursor,
    validate_application_inputs,
)
from jobconnect.modules.invites.schemas import InviteAcceptResponse, InviteDetail, InviteRejectRequest, InviteRequest
from jobconnect.modules.jobs.service import get_job_row, job_summary
from jobconnect.modules.resumes.service import get_resume_row, resume_summary


INVITE_DETAIL_SELECT = """
    i.invite_id, i.job_id, i.resume_id, i.candidate_user_id, i.recruiter_user_id,
    i.status, i.message, i.created_at, i.updated_at,
    j.job_id, j.title, j.location, j.job_type, j.seniority, j.education,
    j.skills, j.required_certifications, j.status, j.published_at,
    r.resume_id, r.title, r.location, r.job_type, r.seniority, r.education,
    r.skills, r.certifications, r.status
"""


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def invite_detail(row: tuple) -> InviteDetail:
    job = job_summary(row[9:19]) if len(row) >= 19 else None
    resume = resume_summary(row[19:28]) if len(row) >= 28 else None
    return InviteDetail(
        invite_id=row[0],
        job_id=row[1],
        resume_id=row[2],
        candidate_user_id=row[3],
        recruiter_user_id=row[4],
        status=row[5],
        message=row[6],
        created_at=_dt(row[7]) if len(row) > 7 else None,
        updated_at=_dt(row[8]) if len(row) > 8 else None,
        job_summary=job,
        resume_summary=resume,
    )


def invite_visibility(user: CurrentUser, status: Any, job_id: Any, resume_id: Any):
    if user.role == "candidate":
        where = ["i.candidate_user_id = %s"]
        params: list[Any] = [user.user_id]
    elif user.role == "recruiter":
        where = ["i.recruiter_user_id = %s"]
        params = [user.user_id]
    else:
        where = ["TRUE"]
        params = []
    if status:
        where.append("i.status = %s")
        params.append(status)
    if job_id:
        where.append("i.job_id = %s")
        params.append(job_id)
    if resume_id:
        where.append("i.resume_id = %s")
        params.append(resume_id)
    return " AND ".join(where), params


def get_invite_row(invite_id: int, user: CurrentUser) -> Optional[tuple]:
    where, params = invite_visibility(user, None, None, None)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {INVITE_DETAIL_SELECT}
            FROM recruiter_invites i
            JOIN job_posts j USING (job_id)
            JOIN candidate_resumes r USING (resume_id)
            WHERE {where} AND i.invite_id = %s
            """,
            (*params, invite_id),
        )
        return cur.fetchone()


def _select_invite_by_id(cur: Any, invite_id: int) -> Optional[tuple]:
    cur.execute(
        f"""
        SELECT {INVITE_DETAIL_SELECT}
        FROM recruiter_invites i
        JOIN job_posts j USING (job_id)
        JOIN candidate_resumes r USING (resume_id)
        WHERE i.invite_id = %s
        """,
        (invite_id,),
    )
    return cur.fetchone()


def list_invites(
    status: Optional[str],
    job_id: Optional[int],
    resume_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = invite_visibility(user, status, job_id, resume_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM recruiter_invites i JOIN job_posts j USING (job_id) WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT {INVITE_DETAIL_SELECT}
            FROM recruiter_invites i
            JOIN job_posts j USING (job_id)
            JOIN candidate_resumes r USING (resume_id)
            WHERE {where}
            ORDER BY i.invite_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [invite_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def create_invite(request: InviteRequest, user: CurrentUser) -> InviteDetail:
    resume = get_resume_row(request.resume_id)
    job = get_job_row(request.job_id)
    if resume is None:
        raise business_error(404, "not_found", "Resume not found.")
    if resume[12] != "active":
        raise business_error(400, "inactive_resume", "Invites require an active resume.")
    if job is None:
        raise business_error(404, "not_found", "Job not found.")
    if job[2] != user.user_id:
        raise business_error(403, "forbidden", "Recruiters can invite only for their own jobs.")
    if job[11] == "closed":
        raise business_error(409, "job_closed", "Closed jobs do not accept invites.")
    if job[11] != "published":
        raise business_error(400, "invalid_job_state", "Invites require a published job.")

    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM recruiter_invites
             WHERE job_id = %s AND resume_id = %s AND status = 'pending'
            """,
            (request.job_id, request.resume_id),
        )
        if cur.fetchone() is not None:
            raise business_error(409, "duplicate_invite", "A pending invite already exists for this job and resume.")

        cur.execute(
            """
            INSERT INTO recruiter_invites
                (job_id, resume_id, candidate_user_id, recruiter_user_id, message)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message
            """,
            (request.job_id, request.resume_id, resume[1], user.user_id, request.message),
        )
        row = cur.fetchone()
        notify(
            cur,
            resume[1],
            "recruiter_invite_sent",
            "Recruiter invite sent",
            "A recruiter invited you to apply.",
            "invite",
            row[0],
            actor_id=user.user_id,
            metadata={
                "invite_id": row[0],
                "job_id": request.job_id,
                "resume_id": request.resume_id,
                "candidate_user_id": resume[1],
                "recruiter_user_id": user.user_id,
            },
        )
        from jobconnect.modules.api.shared import audit

        audit(
            cur,
            user.user_id,
            "recruiter_invite_sent",
            "invite",
            row[0],
            metadata={
                "job_id": request.job_id,
                "resume_id": request.resume_id,
                "candidate_user_id": resume[1],
                "recruiter_user_id": user.user_id,
            },
        )
        detail_row = _select_invite_by_id(cur, row[0])
        if detail_row is None:
            raise business_error(500, "invite_create_failed", "Invite was not readable after creation.")
    return invite_detail(detail_row)


def get_invite(invite_id: int, user: CurrentUser) -> InviteDetail:
    row = get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    return invite_detail(row)


def accept_invite(invite_id: int, user: CurrentUser) -> InviteAcceptResponse:
    row = get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    if row[5] != "pending":
        raise business_error(409, "invalid_state", "Invite is not pending.")
    _resume, job = validate_application_inputs(row[1], row[2], row[3])
    with _api().get_connection() as conn, conn.cursor() as cur:
        app = create_application_in_cursor(
            cur,
            row[1],
            row[2],
            row[3],
            user.user_id,
            "Accepted invite",
            job[2],
            allow_existing=True,
        )
        cur.execute(
            """
            UPDATE recruiter_invites
               SET status = 'accepted', updated_at = now()
             WHERE invite_id = %s AND status = 'pending'
             RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message
            """,
            (invite_id,),
        )
        updated = cur.fetchone()
        if updated is None:
            raise business_error(409, "invalid_state", "Invite is not pending.")
        notify(
            cur,
            updated[4],
            "invite_accepted",
            "Invite accepted",
            "Candidate accepted your invite.",
            "invite",
            invite_id,
            actor_id=user.user_id,
            metadata={
                "invite_id": invite_id,
                "job_id": updated[1],
                "resume_id": updated[2],
                "candidate_user_id": updated[3],
                "recruiter_user_id": updated[4],
                "application_id": app[0],
            },
        )
        from jobconnect.modules.api.shared import audit

        audit(
            cur,
            user.user_id,
            "invite_accepted",
            "invite",
            invite_id,
            metadata={
                "job_id": updated[1],
                "resume_id": updated[2],
                "candidate_user_id": updated[3],
                "recruiter_user_id": updated[4],
                "application_id": app[0],
            },
        )
        detail_row = _select_invite_by_id(cur, invite_id)
        if detail_row is None:
            raise business_error(500, "invite_update_failed", "Invite was not readable after acceptance.")
    return InviteAcceptResponse(invite=invite_detail(detail_row), application=application_detail(app))


def reject_invite(invite_id: int, request: InviteRejectRequest, user: CurrentUser) -> InviteDetail:
    row = get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    if row[5] != "pending":
        raise business_error(409, "invalid_state", "Invite is not pending.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE recruiter_invites
               SET status = 'rejected', updated_at = now()
             WHERE invite_id = %s AND status = 'pending'
             RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message
            """,
            (invite_id,),
        )
        updated = cur.fetchone()
        if updated is None:
            raise business_error(409, "invalid_state", "Invite is not pending.")
        notify(
            cur,
            updated[4],
            "invite_rejected",
            "Invite rejected",
            request.note or "Candidate rejected your invite.",
            "invite",
            invite_id,
            actor_id=user.user_id,
            metadata={
                "invite_id": invite_id,
                "job_id": updated[1],
                "resume_id": updated[2],
                "candidate_user_id": updated[3],
                "recruiter_user_id": updated[4],
            },
        )
        from jobconnect.modules.api.shared import audit

        audit(
            cur,
            user.user_id,
            "invite_rejected",
            "invite",
            invite_id,
            metadata={
                "job_id": updated[1],
                "resume_id": updated[2],
                "candidate_user_id": updated[3],
                "recruiter_user_id": updated[4],
            },
        )
        detail_row = _select_invite_by_id(cur, invite_id)
        if detail_row is None:
            raise business_error(500, "invite_update_failed", "Invite was not readable after rejection.")
    return invite_detail(detail_row)
