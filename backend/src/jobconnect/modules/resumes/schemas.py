from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, Education, JobType, Location, ResumeStatus, Seniority


class ResumeRequest(APIModel):
    title: str = Field(min_length=1)
    summary: str = ""
    experience: str = ""
    skills: list[str] = Field(default_factory=list)
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    certifications: list[str] = Field(default_factory=list)
    is_primary: bool = False


class ResumeUpdateRequest(APIModel):
    title: Optional[str] = Field(default=None, min_length=1)
    summary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[list[str]] = None
    location: Optional[Location] = None
    job_type: Optional[JobType] = None
    seniority: Optional[Seniority] = None
    education: Optional[Education] = None
    certifications: Optional[list[str]] = None
    is_primary: Optional[bool] = None


class ResumeSummary(APIModel):
    resume_id: int
    title: str
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    status: ResumeStatus


class ResumeDetail(ResumeSummary):
    candidate_user_id: int
    summary: str
    experience: str
    is_primary: bool


class SemanticResumeItem(ResumeSummary):
    relevance_score: float


class SemanticResumeSearchResponse(APIModel):
    items: list[SemanticResumeItem]
    total: int
    limit: int
    offset: int
