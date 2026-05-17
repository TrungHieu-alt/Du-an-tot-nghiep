from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.admin import service
from jobconnect.modules.admin.schemas import AdminUserDetail, AdminUserUpdateRequest
from jobconnect.modules.api.shared import (
    ApplicationStatus,
    CurrentUser,
    InviteStatus,
    NotificationStatus,
    Paginated,
    ParseStatus,
    Role,
    UserStatus,
    business_error,
    require_roles,
)
from jobconnect.modules.auth.schemas import UserSummary

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=Paginated)
def admin_users(
    role: Optional[Role] = None,
    status: Optional[UserStatus] = None,
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_users(role, status, q, limit, offset, user)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def admin_user_detail(user_id: int, user: CurrentUser = Depends(require_roles("admin"))):
    return service.admin_user_detail(user_id, user)


@router.patch("/users/{user_id}", response_model=UserSummary)
def admin_update_user(
    user_id: int,
    request: AdminUserUpdateRequest,
    user: CurrentUser = Depends(require_roles("admin")),
):
    if request.status is None:
        raise business_error(400, "no_fields", "No updatable fields provided.")
    return service.update_user_status(user_id, request.status, user)


@router.get("/documents", response_model=Paginated)
def admin_documents(
    document_type: Optional[Literal["candidate_resume", "job_post"]] = None,
    parse_status: Optional[ParseStatus] = None,
    owner_user_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_documents(document_type, parse_status, owner_user_id, limit, offset, user)


@router.get("/parse-jobs", response_model=Paginated)
def admin_parse_jobs(
    status: Optional[ParseStatus] = None,
    document_type: Optional[Literal["candidate_resume", "job_post"]] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_parse_jobs(status, document_type, limit, offset, user)


@router.get("/applications", response_model=Paginated)
def admin_applications(
    status: Optional[ApplicationStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_applications(status, job_id, resume_id, limit, offset, user)


@router.get("/invites", response_model=Paginated)
def admin_invites(
    status: Optional[InviteStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_invites(status, job_id, resume_id, limit, offset, user)


@router.get("/notifications", response_model=Paginated)
def admin_notifications(
    status: Optional[NotificationStatus] = None,
    user_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_notifications(status, user_id, limit, offset, user)


@router.get("/audit-logs", response_model=Paginated)
def admin_audit_logs(
    actor_user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    return service.admin_audit_logs(actor_user_id, target_type, target_id, event_type, limit, offset, user)
