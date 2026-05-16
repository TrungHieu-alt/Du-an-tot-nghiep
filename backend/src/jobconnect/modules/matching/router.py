from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from jobconnect.modules.api.shared import CurrentUser, require_roles
from jobconnect.modules.matching import service
from jobconnect.modules.matching.schemas import MatchingRequest, MatchingResponse

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/jobs/{job_id}/run", response_model=MatchingResponse)
def run_job_matching(
    job_id: int,
    request: MatchingRequest = Body(default_factory=MatchingRequest),
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.run_job_matching(job_id, request, user)


@router.post("/resumes/{resume_id}/run", response_model=MatchingResponse)
def run_resume_matching(
    resume_id: int,
    request: MatchingRequest = Body(default_factory=MatchingRequest),
    user: CurrentUser = Depends(require_roles("candidate", "admin")),
):
    return service.run_resume_matching(resume_id, request, user)
