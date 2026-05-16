from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.api.shared import CurrentUser, Paginated, require_active, require_roles
from jobconnect.modules.jobs import service
from jobconnect.modules.jobs.schemas import (
    JobDetail,
    JobRequest,
    JobStatus,
    JobUpdateRequest,
    SemanticJobSearchResponse,
)
from jobconnect.modules.matching.schemas import SemanticSearchRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=Paginated)
def list_jobs(
    status: Optional[JobStatus] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    seniority: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.list_jobs(status, location, job_type, seniority, q, limit, offset, user)


@router.post("", response_model=JobDetail, status_code=201)
def create_job(request: JobRequest, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    return service.create_job(request, user)


@router.get("/search", response_model=Paginated)
def search_jobs(
    q: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    seniority: Optional[str] = None,
    status: Optional[JobStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    return service.search_jobs(q, location, job_type, seniority, status, limit, offset, user)


@router.post("/semantic-search", response_model=SemanticJobSearchResponse)
def semantic_search_jobs(request: SemanticSearchRequest, user: CurrentUser = Depends(require_active)):
    return service.semantic_search_jobs(request, user)


@router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_job(job_id, user)


@router.patch("/{job_id}", response_model=JobDetail)
def update_job(
    job_id: int,
    request: JobUpdateRequest,
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.update_job(job_id, request, user)


@router.post("/{job_id}/publish", response_model=JobDetail)
def publish_job(job_id: int, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    return service.publish_job(job_id, user)


@router.post("/{job_id}/close", response_model=JobDetail)
def close_job(job_id: int, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    return service.close_job(job_id, user)
