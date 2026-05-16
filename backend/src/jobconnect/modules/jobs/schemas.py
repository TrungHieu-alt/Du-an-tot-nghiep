from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, Education, JobStatus, JobType, Location, Seniority


class JobRequest(APIModel):
    organization_id: int
    title: str = Field(min_length=1)
    requirement: str = ""
    skills: list[str] = Field(default_factory=list)
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    required_certifications: list[str] = Field(default_factory=list)
    expires_at: Optional[str] = None


class JobUpdateRequest(APIModel):
    organization_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1)
    requirement: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[Location] = None
    job_type: Optional[JobType] = None
    seniority: Optional[Seniority] = None
    education: Optional[Education] = None
    required_certifications: Optional[list[str]] = None
    expires_at: Optional[str] = None


class JobSummary(APIModel):
    job_id: int
    title: str
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    status: JobStatus
    published_at: Optional[str] = None


class JobDetail(JobSummary):
    organization_id: int
    recruiter_user_id: int
    requirement: str
    expires_at: Optional[str] = None


class SemanticJobItem(JobSummary):
    relevance_score: float


class SemanticJobSearchResponse(APIModel):
    items: list[SemanticJobItem]
    total: int
    limit: int
    offset: int
