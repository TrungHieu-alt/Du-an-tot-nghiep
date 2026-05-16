from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, Location
from jobconnect.modules.auth.schemas import UserSummary
from jobconnect.modules.organizations.schemas import Organization


class CandidateProfileRequest(APIModel):
    full_name: str = Field(min_length=1)
    phone: Optional[str] = None
    current_location: Optional[Location] = None
    total_experience_years: Optional[int] = Field(default=None, ge=0)
    headline: Optional[str] = None


class CandidateProfile(CandidateProfileRequest):
    user_id: int


class RecruiterProfileRequest(APIModel):
    organization_id: int
    full_name: str = Field(min_length=1)
    title: Optional[str] = None
    phone: Optional[str] = None


class RecruiterProfile(RecruiterProfileRequest):
    user_id: int


class MeResponse(APIModel):
    user: UserSummary
    candidate_profile: Optional[CandidateProfile] = None
    recruiter_profile: Optional[RecruiterProfile] = None
    organization: Optional[Organization] = None
