from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.api.shared import CurrentUser, Paginated, require_active, require_roles
from jobconnect.modules.matching.schemas import SemanticSearchRequest
from jobconnect.modules.resumes import service
from jobconnect.modules.resumes.schemas import (
    ResumeDetail,
    ResumeRequest,
    ResumeStatus,
    ResumeUpdateRequest,
    SemanticResumeSearchResponse,
)

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/resumes", response_model=Paginated)
def list_resumes(
    status: Optional[ResumeStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("candidate", "admin")),
):
    return service.list_resumes(status, limit, offset, user)


@router.post("/resumes", response_model=ResumeDetail, status_code=201)
def create_resume(request: ResumeRequest, user: CurrentUser = Depends(require_roles("candidate"))):
    return service.create_resume(request, user)


@router.get("/resumes/search", response_model=Paginated)
def search_resumes(
    q: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    seniority: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.search_resumes(q, location, job_type, seniority, limit, offset)


@router.post("/resumes/semantic-search", response_model=SemanticResumeSearchResponse)
def semantic_search_resumes(
    request: SemanticSearchRequest,
    _: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.semantic_search_resumes(request)


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: int, user: CurrentUser = Depends(require_active)):
    return service.get_resume(resume_id, user)


@router.patch("/resumes/{resume_id}", response_model=ResumeDetail)
def update_resume(
    resume_id: int,
    request: ResumeUpdateRequest,
    user: CurrentUser = Depends(require_roles("candidate")),
):
    return service.update_resume(resume_id, request, user)


@router.post("/resumes/{resume_id}/activate", response_model=ResumeDetail)
def activate_resume(resume_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    return service.activate_resume(resume_id, user)


@router.post("/resumes/{resume_id}/archive", response_model=ResumeDetail)
def archive_resume(resume_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    return service.archive_resume(resume_id, user)
