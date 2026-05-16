from __future__ import annotations

from typing import Optional

from jobconnect.modules.api.shared import APIModel, InviteStatus
from jobconnect.modules.applications.schemas import ApplicationDetail
from jobconnect.modules.jobs.schemas import JobSummary
from jobconnect.modules.resumes.schemas import ResumeSummary


class InviteRequest(APIModel):
    job_id: int
    resume_id: int
    message: Optional[str] = None


class InviteRejectRequest(APIModel):
    note: Optional[str] = None


class InviteDetail(APIModel):
    invite_id: int
    job_id: int
    resume_id: int
    candidate_user_id: int
    recruiter_user_id: int
    status: InviteStatus
    message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    job_summary: Optional[JobSummary] = None
    resume_summary: Optional[ResumeSummary] = None


class InviteAcceptResponse(APIModel):
    invite: InviteDetail
    application: ApplicationDetail


class InviteListResponse(APIModel):
    items: list[InviteDetail]
    total: int
    limit: int
    offset: int
