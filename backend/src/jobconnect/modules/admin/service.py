from __future__ import annotations

from typing import Any, Literal, Optional

from jobconnect.modules.admin.schemas import AdminUserDetail
from jobconnect.modules.api.shared import (
    ApplicationStatus,
    CurrentUser,
    InviteStatus,
    NotificationStatus,
    Paginated,
    ParseStatus,
    Role,
    UserStatus,
    _dt,
    admin_filters,
    admin_user_ops_summary,
    audit,
    business_error,
)
from jobconnect.modules.applications.service import application_detail
from jobconnect.modules.auth.service import user_summary
from jobconnect.modules.documents.service import document_detail, parse_job_detail
from jobconnect.modules.invites.service import invite_detail
from jobconnect.modules.notifications.service import notification_detail
from jobconnect.modules.organizations.schemas import Organization
from jobconnect.modules.users.schemas import CandidateProfile, RecruiterProfile


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def admin_users(
    role: Optional[Role],
    status: Optional[UserStatus],
    q: Optional[str],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(role=role, status=status, q=q)
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(cur, user.user_id, "admin_monitoring_access", "users", None)
        cur.execute(f"SELECT COUNT(*) FROM users WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT user_id, email, role, status, created_at FROM users WHERE {where} ORDER BY user_id ASC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [user_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_user_detail(user_id: int, user: CurrentUser) -> AdminUserDetail:
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(cur, user.user_id, "admin_monitoring_access", "user", user_id)
        cur.execute("SELECT user_id, email, role, status, created_at FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if row is None:
            raise business_error(404, "not_found", "User not found.")
        summary = user_summary(row)
        candidate_profile = None
        recruiter_profile = None
        organization = None
        if summary.role == "candidate":
            cur.execute(
                """
                SELECT user_id, full_name, phone, current_location, total_experience_years, headline
                  FROM candidate_profiles WHERE user_id = %s
                """,
                (user_id,),
            )
            profile = cur.fetchone()
            if profile:
                candidate_profile = CandidateProfile(
                    user_id=profile[0],
                    full_name=profile[1],
                    phone=profile[2],
                    current_location=profile[3],
                    total_experience_years=profile[4],
                    headline=profile[5],
                )
        elif summary.role == "recruiter":
            cur.execute(
                """
                SELECT rp.user_id, rp.organization_id, rp.full_name, rp.title, rp.phone,
                       o.organization_id, o.name, o.slug, o.logo_url, o.about
                  FROM recruiter_profiles rp
                  JOIN organizations o ON o.organization_id = rp.organization_id
                 WHERE rp.user_id = %s
                """,
                (user_id,),
            )
            profile = cur.fetchone()
            if profile:
                recruiter_profile = RecruiterProfile(
                    user_id=profile[0],
                    organization_id=profile[1],
                    full_name=profile[2],
                    title=profile[3],
                    phone=profile[4],
                )
                organization = Organization(
                    organization_id=profile[5],
                    name=profile[6],
                    slug=profile[7],
                    logo_url=profile[8],
                    about=profile[9],
                )
        ops_summary = admin_user_ops_summary(cur, user_id)
    return AdminUserDetail(
        user=summary,
        candidate_profile=candidate_profile,
        recruiter_profile=recruiter_profile,
        organization=organization,
        ops_summary=ops_summary,
    )


def admin_documents(
    document_type: Optional[Literal["candidate_resume", "job_post"]],
    parse_status: Optional[ParseStatus],
    owner_user_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(
        document_type=document_type,
        owner_user_id=owner_user_id,
        parse_status=parse_status,
    )
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(cur, user.user_id, "admin_monitoring_access", "documents", None)
        cur.execute(f"SELECT COUNT(*) FROM uploaded_documents WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT document_id, owner_user_id, document_type, object_key, file_url,
                   original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            FROM uploaded_documents WHERE {where} ORDER BY document_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [document_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_parse_jobs(
    status: Optional[ParseStatus],
    document_type: Optional[Literal["candidate_resume", "job_post"]],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(status=status, document_type=document_type)
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(cur, user.user_id, "admin_monitoring_access", "parse_jobs", None)
        cur.execute(
            f"""
            SELECT COUNT(*) FROM parse_jobs
            JOIN uploaded_documents USING (document_id)
            WHERE {where}
            """,
            params,
        )
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT parse_jobs.parse_job_id, parse_jobs.document_id, parse_jobs.target_entity_type,
                   parse_jobs.resume_id, parse_jobs.job_id, parse_jobs.status,
                   parse_jobs.error_code, parse_jobs.error_message,
                   parse_jobs.created_at, parse_jobs.updated_at
            FROM parse_jobs
            JOIN uploaded_documents USING (document_id)
            WHERE {where} ORDER BY parse_job_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [parse_job_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_applications(
    status: Optional[ApplicationStatus],
    job_id: Optional[int],
    resume_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(status=status, job_id=job_id, resume_id=resume_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(
            cur,
            user.user_id,
            "admin_monitoring_access",
            "applications",
            None,
            metadata={"status": status, "job_id": job_id, "resume_id": resume_id},
        )
        cur.execute(f"SELECT COUNT(*) FROM applications WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT application_id, job_id, candidate_user_id, resume_id, status FROM applications WHERE {where} ORDER BY application_id DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [application_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_invites(
    status: Optional[InviteStatus],
    job_id: Optional[int],
    resume_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(status=status, job_id=job_id, resume_id=resume_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(
            cur,
            user.user_id,
            "admin_monitoring_access",
            "invites",
            None,
            metadata={"status": status, "job_id": job_id, "resume_id": resume_id},
        )
        cur.execute(f"SELECT COUNT(*) FROM recruiter_invites WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message FROM recruiter_invites WHERE {where} ORDER BY invite_id DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [invite_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_notifications(
    status: Optional[NotificationStatus],
    user_id: Optional[int],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(status=status, recipient_user_id=user_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(
            cur,
            user.user_id,
            "admin_monitoring_access",
            "notifications",
            None,
            metadata={"status": status, "recipient_user_id": user_id},
        )
        cur.execute(f"SELECT COUNT(*) FROM notifications WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT notification_id, recipient_user_id, type, status, title, body,
                   entity_type, entity_id, email_delivery_status, metadata
            FROM notifications WHERE {where} ORDER BY notification_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [notification_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def admin_audit_logs(
    actor_user_id: Optional[int],
    target_type: Optional[str],
    target_id: Optional[int],
    event_type: Optional[str],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where, params = admin_filters(
        actor_user_id=actor_user_id,
        target_entity_type=target_type,
        target_entity_id=target_id,
        event_type=event_type,
    )
    with _api().get_connection() as conn, conn.cursor() as cur:
        audit(
            cur,
            user.user_id,
            "admin_monitoring_access",
            "audit_logs",
            None,
            metadata={
                "actor_user_id": actor_user_id,
                "target_type": target_type,
                "target_id": target_id,
                "event_type": event_type,
            },
        )
        cur.execute(f"SELECT COUNT(*) FROM audit_logs WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT audit_log_id, actor_user_id, event_type, target_entity_type,
                   target_entity_id, metadata, created_at
            FROM audit_logs WHERE {where} ORDER BY audit_log_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [
            {
                "audit_log_id": r[0],
                "actor_user_id": r[1],
                "event_type": r[2],
                "target_entity_type": r[3],
                "target_entity_id": r[4],
                "metadata": r[5],
                "created_at": _dt(r[6]),
            }
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def update_user_status(
    target_user_id: int,
    new_status: UserStatus,
    admin_user: CurrentUser,
) -> Any:
    """Admin sets a user's status (active/invited/disabled). Writes audit row.

    Prevents an admin from disabling themselves to avoid lockout.
    """
    if target_user_id == admin_user.user_id and new_status == "disabled":
        raise business_error(
            400, "self_disable_forbidden", "Admins cannot disable their own account."
        )
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, status FROM users WHERE user_id = %s",
            (target_user_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise business_error(404, "not_found", "User not found.")
        previous_status = row[1]
        cur.execute(
            "UPDATE users SET status = %s WHERE user_id = %s RETURNING user_id, email, role, status, created_at",
            (new_status, target_user_id),
        )
        updated = cur.fetchone()
        audit(
            cur,
            admin_user.user_id,
            "admin_user_status_changed",
            "user",
            target_user_id,
            metadata={
                "from_status": previous_status,
                "to_status": new_status,
            },
        )
    return user_summary(updated)
