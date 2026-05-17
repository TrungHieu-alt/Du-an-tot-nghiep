from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.api.shared import ApplicationStatus, CurrentUser, require_active, require_roles
from jobconnect.modules.applications import service
from jobconnect.modules.applications.schemas import (
    ApplicationDetail,
    ApplicationListResponse,
    ApplicationRequest,
    ApplicationSummary,
    ApplicationStatusRequest,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    status: Optional[ApplicationStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.list_applications(status, job_id, resume_id, limit, offset, user)


@router.post("", response_model=ApplicationSummary, status_code=201)
def create_application(request: ApplicationRequest, user: CurrentUser = Depends(require_roles("candidate"))):
    return service.create_application(request, user)


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(application_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_application(application_id, user)


@router.post("/{application_id}/status", response_model=ApplicationDetail)
def update_application_status(
    application_id: int,
    request: ApplicationStatusRequest,
    user: CurrentUser = Depends(require_active),
):
    return service.update_application_status(application_id, request, user)
