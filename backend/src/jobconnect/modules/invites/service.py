from __future__ import annotations

from typing import Any, Optional

from jobconnect.modules.api.shared import CurrentUser, Paginated, business_error, dispatch_email, notify
from jobconnect.modules.applications.service import application_detail, create_application_record
from jobconnect.modules.invites.schemas import InviteAcceptResponse, InviteDetail, InviteRejectRequest, InviteRequest
from jobconnect.modules.jobs.service import get_job_row
from jobconnect.modules.resumes.service import get_resume_row


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def invite_detail(row: tuple) -> InviteDetail:
    return InviteDetail(
        invite_id=row[0],
        job_id=row[1],
        resume_id=row[2],
        candidate_user_id=row[3],
        recruiter_user_id=row[4],
        status=row[5],
        message=row[6],
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
            SELECT i.invite_id, i.job_id, i.resume_id, i.candidate_user_id, i.recruiter_user_id, i.status, i.message
            FROM recruiter_invites i JOIN job_posts j USING (job_id)
            WHERE {where} AND i.invite_id = %s
            """,
            (*params, invite_id),
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
            SELECT i.invite_id, i.job_id, i.resume_id, i.candidate_user_id, i.recruiter_user_id, i.status, i.message
            FROM recruiter_invites i JOIN job_posts j USING (job_id)
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
    if resume is None or resume[12] != "active":
        raise business_error(404, "not_found", "Active resume not found.")
    # Slice 9: closed jobs (409 closed_job) vs missing/draft (404 not_found)
    if job is None:
        raise business_error(404, "not_found", "Published job not found.")
    if job[11] == "closed":
        raise business_error(409, "closed_job", "Job is closed and cannot send new invites.")
    if job[11] != "published":
        raise business_error(404, "not_found", "Published job not found.")
    if job[2] != user.user_id:
        raise business_error(403, "forbidden", "Recruiters can invite only for their own jobs.")

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
        notif_id = notify(cur, resume[1], "recruiter_invite_sent", "Recruiter invite sent", "A recruiter invited you to apply.", "invite", row[0])
        from jobconnect.modules.api.shared import audit

        audit(cur, user.user_id, "recruiter_invite_sent", "invite", row[0])
    dispatch_email(notif_id)
    return invite_detail(row)


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
    # Slice 9: prevent accepting an invite whose job has since been closed.
    # Without this check the invite would flip to 'accepted' but the downstream
    # application creation would fail with 409, leaving inconsistent state.
    job = get_job_row(row[1])  # row[1] = job_id
    if job is None:
        raise business_error(404, "not_found", "Job not found.")
    if job[11] == "closed":
        raise business_error(409, "closed_job", "Job is closed; invite cannot be accepted.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE recruiter_invites SET status = 'accepted', updated_at = now() WHERE invite_id = %s RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message",
            (invite_id,),
        )
        updated = cur.fetchone()
        notif_id = notify(cur, updated[4], "invite_accepted", "Invite accepted", "Candidate accepted your invite.", "invite", invite_id)
        from jobconnect.modules.api.shared import audit

        audit(cur, user.user_id, "invite_accepted", "invite", invite_id)
    dispatch_email(notif_id)
    app = create_application_record(updated[1], updated[2], updated[3], user.user_id, "Accepted invite", allow_existing=True)
    return InviteAcceptResponse(invite=invite_detail(updated), application=application_detail(app))


def reject_invite(invite_id: int, request: InviteRejectRequest, user: CurrentUser) -> InviteDetail:
    row = get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    if row[5] != "pending":
        raise business_error(409, "invalid_state", "Invite is not pending.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE recruiter_invites SET status = 'rejected', updated_at = now() WHERE invite_id = %s RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message",
            (invite_id,),
        )
        updated = cur.fetchone()
        notif_id = notify(cur, updated[4], "invite_rejected", "Invite rejected", request.note or "Candidate rejected your invite.", "invite", invite_id)
        from jobconnect.modules.api.shared import audit

        audit(cur, user.user_id, "invite_rejected", "invite", invite_id)
    dispatch_email(notif_id)
    return invite_detail(updated)
