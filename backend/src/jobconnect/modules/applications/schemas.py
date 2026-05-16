from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, ApplicationStatus


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


class ApplicationDetail(APIModel):
    application_id: int
    job_id: int
    candidate_user_id: int
    resume_id: int
    status: ApplicationStatus
    events: list[ApplicationEvent] = Field(default_factory=list)
