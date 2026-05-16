from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query

from jobconnect.modules.api.shared import CurrentUser, InviteStatus, Paginated, require_active, require_roles
from jobconnect.modules.invites import service
from jobconnect.modules.invites.schemas import InviteAcceptResponse, InviteDetail, InviteRejectRequest, InviteRequest

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("", response_model=Paginated)
def list_invites(
    status: Optional[InviteStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.list_invites(status, job_id, resume_id, limit, offset, user)


@router.post("", response_model=InviteDetail, status_code=201)
def create_invite(request: InviteRequest, user: CurrentUser = Depends(require_roles("recruiter"))):
    return service.create_invite(request, user)


@router.get("/{invite_id}", response_model=InviteDetail)
def get_invite(invite_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_invite(invite_id, user)


@router.post("/{invite_id}/accept", response_model=InviteAcceptResponse)
def accept_invite(invite_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    return service.accept_invite(invite_id, user)


@router.post("/{invite_id}/reject", response_model=InviteDetail)
def reject_invite(
    invite_id: int,
    request: InviteRejectRequest = Body(default_factory=InviteRejectRequest),
    user: CurrentUser = Depends(require_roles("candidate")),
):
    return service.reject_invite(invite_id, request, user)
