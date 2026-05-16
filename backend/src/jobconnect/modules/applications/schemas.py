from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, ApplicationStatus
from jobconnect.modules.jobs.schemas import JobSummary
from jobconnect.modules.resumes.schemas import ResumeSummary


class ApplicationRequest(APIModel):
    job_id: int
    resume_id: int
    note: Optional[str] = None


class ApplicationStatusRequest(APIModel):
    status: ApplicationStatus
    note: Optional[str] = None


class ApplicationEvent(APIModel):
    event_id: int
    from_status: Optional[ApplicationStatus] = None
    to_status: ApplicationStatus
    actor_user_id: Optional[int] = None
    note: Optional[str] = None
    created_at: str


class ApplicationSummary(APIModel):
    application_id: int
    job_id: int
    candidate_user_id: int
    resume_id: int
    status: ApplicationStatus
    applied_at: Optional[str] = None
    updated_at: Optional[str] = None
    job_summary: Optional[JobSummary] = None
    resume_summary: Optional[ResumeSummary] = None


class ApplicationDetail(ApplicationSummary):
    events: list[ApplicationEvent] = Field(default_factory=list)


class ApplicationListResponse(APIModel):
    items: list[ApplicationSummary]
    total: int
    limit: int
    offset: int
