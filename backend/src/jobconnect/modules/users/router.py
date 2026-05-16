from __future__ import annotations

from fastapi import APIRouter, Depends

from jobconnect.modules.api.shared import CurrentUser, current_user, require_roles
from jobconnect.modules.users import service
from jobconnect.modules.users.schemas import (
    CandidateProfile,
    CandidateProfileRequest,
    MeResponse,
    RecruiterProfile,
    RecruiterProfileRequest,
)

me_router = APIRouter(tags=["me"])
candidate_router = APIRouter(prefix="/candidate", tags=["candidate"])
recruiter_router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@me_router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(current_user)) -> MeResponse:
    return service.me(user)


@candidate_router.get("/profile", response_model=CandidateProfile)
def get_candidate_profile(user: CurrentUser = Depends(require_roles("candidate"))):
    return service.get_candidate_profile(user)


@candidate_router.put("/profile", response_model=CandidateProfile)
def put_candidate_profile(
    request: CandidateProfileRequest,
    user: CurrentUser = Depends(require_roles("candidate")),
):
    return service.put_candidate_profile(request, user)


@recruiter_router.get("/profile", response_model=RecruiterProfile)
def get_recruiter_profile(user: CurrentUser = Depends(require_roles("recruiter"))):
    return service.get_recruiter_profile(user)


@recruiter_router.put("/profile", response_model=RecruiterProfile)
def put_recruiter_profile(
    request: RecruiterProfileRequest,
    user: CurrentUser = Depends(require_roles("recruiter")),
):
    return service.put_recruiter_profile(request, user)
