from __future__ import annotations

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, UserStatus
from jobconnect.modules.auth.schemas import UserSummary
from jobconnect.modules.organizations.schemas import Organization
from jobconnect.modules.users.schemas import CandidateProfile, RecruiterProfile


class AdminUserDetail(APIModel):
    user: UserSummary
    candidate_profile: CandidateProfile | None = None
    recruiter_profile: RecruiterProfile | None = None
    organization: Organization | None = None
    ops_summary: dict[str, int] = Field(default_factory=dict)


class AdminUserUpdateRequest(APIModel):
    """PATCH /api/admin/users/{user_id} — admin can enable/disable users."""

    status: UserStatus | None = None
