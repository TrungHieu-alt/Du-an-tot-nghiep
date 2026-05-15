"""Schemas for normal Job CRUD and public job search.

These models are separate from Matching V2. Normal Job data is owned by a
PostgreSQL `users.id` through `created_by` and powers the regular multi-
industry search flow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


JobStatus = str
JobVisibility = str


class LocationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str | None = None
    state: str | None = None
    country: str | None = None
    remote_type: str | None = None


class JobSkillPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    normalized_name: str | None = None
    level: str | None = None
    category: str | None = None


class WeightedJobSkillPayload(JobSkillPayload):
    weight: int | None = Field(default=None, ge=0)


class SalaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)
    currency: str | None = None
    period: str | None = None


class RequiredEducationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str | None = None
    major: str | None = None


class RecruiterPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class PreScreenQuestionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str
    type: str | None = None
    required: bool = False
    options: list[str] = Field(default_factory=list)


class JobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str | None = None
    title: str = Field(min_length=1, max_length=255)
    slug: str | None = None
    status: JobStatus = "draft"
    visibility: JobVisibility = "private"
    company_name: str | None = None
    company_logo_url: str | None = None
    company_website: str | None = None
    company_location: str | None = None
    company_size: str | None = None
    company_industry: str | None = None
    industry: str | None = None
    occupation_group: str | None = None
    department: str | None = None
    location: LocationPayload = Field(default_factory=LocationPayload)
    employment_type: list[str] = Field(default_factory=list)
    seniority: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    skills: list[JobSkillPayload] = Field(default_factory=list)
    must_have_skills: list[WeightedJobSkillPayload] = Field(default_factory=list)
    nice_to_have_skills: list[WeightedJobSkillPayload] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0)
    education_level: str | None = None
    required_education: RequiredEducationPayload = Field(default_factory=RequiredEducationPayload)
    required_certifications: list[str] = Field(default_factory=list)
    salary: SalaryPayload = Field(default_factory=SalaryPayload)
    benefits: list[str] = Field(default_factory=list)
    bonus: str | None = None
    equity: str | None = None
    apply_url: str | None = None
    apply_email: EmailStr | None = None
    recruiter: RecruiterPayload = Field(default_factory=RecruiterPayload)
    how_to_apply: str | None = None
    application_deadline: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    remote: bool = False
    pre_screen_questions: list[PreScreenQuestionPayload] = Field(default_factory=list)
    required_docs: list[str] = Field(default_factory=list)
    published_by: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    archived: bool = False
    version: int = Field(default=1, ge=1)


class JobUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = None
    status: JobStatus | None = None
    visibility: JobVisibility | None = None
    company_name: str | None = None
    company_logo_url: str | None = None
    company_website: str | None = None
    company_location: str | None = None
    company_size: str | None = None
    company_industry: str | None = None
    industry: str | None = None
    occupation_group: str | None = None
    department: str | None = None
    location: LocationPayload | None = None
    employment_type: list[str] | None = None
    seniority: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    description: str | None = None
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    nice_to_have: list[str] | None = None
    skills: list[JobSkillPayload] | None = None
    must_have_skills: list[WeightedJobSkillPayload] | None = None
    nice_to_have_skills: list[WeightedJobSkillPayload] | None = None
    tools_and_technologies: list[str] | None = None
    domain_knowledge: list[str] | None = None
    experience_years: float | None = Field(default=None, ge=0)
    education_level: str | None = None
    required_education: RequiredEducationPayload | None = None
    required_certifications: list[str] | None = None
    salary: SalaryPayload | None = None
    benefits: list[str] | None = None
    bonus: str | None = None
    equity: str | None = None
    apply_url: str | None = None
    apply_email: EmailStr | None = None
    recruiter: RecruiterPayload | None = None
    how_to_apply: str | None = None
    application_deadline: datetime | None = None
    tags: list[str] | None = None
    categories: list[str] | None = None
    remote: bool | None = None
    pre_screen_questions: list[PreScreenQuestionPayload] | None = None
    required_docs: list[str] | None = None
    published_by: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    archived: bool | None = None
    version: int | None = Field(default=None, ge=1)


class JobResponse(BaseModel):
    id: str
    created_by: str
    company_id: str | None = None
    title: str
    slug: str | None = None
    status: JobStatus
    visibility: JobVisibility
    company_name: str | None = None
    company_logo_url: str | None = None
    company_website: str | None = None
    company_location: str | None = None
    company_size: str | None = None
    company_industry: str | None = None
    industry: str = "unknown"
    occupation_group: str = "unknown"
    department: str | None = None
    location: dict[str, Any] = Field(default_factory=dict)
    employment_type: list[str] = Field(default_factory=list)
    seniority: str | None = None
    team_size: int | None = None
    description: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    skills: list[dict[str, Any]] = Field(default_factory=list)
    must_have_skills: list[dict[str, Any]] = Field(default_factory=list)
    nice_to_have_skills: list[dict[str, Any]] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education_level: str | None = None
    required_education: dict[str, Any] = Field(default_factory=dict)
    required_certifications: list[str] = Field(default_factory=list)
    salary: dict[str, Any] = Field(default_factory=dict)
    benefits: list[str] = Field(default_factory=list)
    bonus: str | None = None
    equity: str | None = None
    apply_url: str | None = None
    apply_email: str | None = None
    recruiter: dict[str, Any] = Field(default_factory=dict)
    how_to_apply: str | None = None
    application_deadline: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    remote: bool = False
    views: int = 0
    applications_count: int = 0
    pre_screen_questions: list[dict[str, Any]] = Field(default_factory=list)
    required_docs: list[str] = Field(default_factory=list)
    published_by: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    archived: bool = False
    version: int = 1
    created_at: datetime
    updated_at: datetime


class JobExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)


class JobExtractResponse(BaseModel):
    extractedText: str
    job: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    rawTextLength: int = 0
    cleanTextLength: int = 0
    preprocessWarnings: list[str] = Field(default_factory=list)
    textQuality: dict[str, Any] = Field(default_factory=dict)
    cleanedText: str = ""


class JobSearchListItem(BaseModel):
    id: str
    job_id: str
    title: str
    company_name: str | None = None
    company_industry: str | None = None
    industry: str = "unknown"
    occupation_group: str = "unknown"
    department: str | None = None
    location: str
    location_detail: dict[str, Any] = Field(default_factory=dict)
    job_type: str
    employment_type: list[str] = Field(default_factory=list)
    working_model: str | None = None
    seniority: str | None = None
    education: str | None = None
    education_level: str | None = None
    skills: list[str] = Field(default_factory=list)
    requirement: str = ""
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tools_and_technologies: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)
    salary: dict[str, Any] = Field(default_factory=dict)
    remote: bool = False


class JobSearchListResponse(BaseModel):
    items: list[JobSearchListItem]
    total: int
    page: int
    limit: int
    totalPages: int
    pagination: dict[str, int] = Field(default_factory=dict)


class JobSearchFiltersResponse(BaseModel):
    industries: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    employmentTypes: list[str] = Field(default_factory=list)
    seniorities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
