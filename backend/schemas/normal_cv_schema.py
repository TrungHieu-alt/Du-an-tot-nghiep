"""Schemas for normal CV CRUD, PDF upload metadata, and candidate search."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from schemas.normal_job_schema import LocationPayload

CvVisibility = Literal["public", "private", "unlisted"]


class CvSkillPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    level: str | None = None
    category: str | None = None
    years: float | None = Field(default=None, ge=0)


class ExperiencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str | None = None
    company: str | None = None
    company_website: str | None = None
    location: str | None = None
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
    is_current: bool = False
    employment_type: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class EducationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: str | None = None
    major: str | None = None
    school: str | None = None
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
    gpa: str | None = None


class ProjectPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    role: str | None = None
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
    tech_stack: list[str] = Field(default_factory=list)
    url: str | None = None
    metrics: list[str] = Field(default_factory=list)


class CertificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    issuer: str | None = None
    issue_date: datetime | None = None
    expiry_date: datetime | None = None
    credential_url: str | None = None


class LanguagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    level: str | None = None


class PortfolioPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_type: str | None = None
    url: str | None = None
    description: str | None = None


class ReferencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    relation: str | None = None
    contact: str | None = None
    note: str | None = None


class CvCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_url: str | None = None
    fullname: str = Field(min_length=1, max_length=255)
    preferred_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: LocationPayload = Field(default_factory=LocationPayload)
    headline: str | None = None
    summary: str | None = None
    target_role: str | None = None
    employment_type: list[str] = Field(default_factory=list)
    salary_expectation: str | None = None
    availability: str | None = None
    skills: list[CvSkillPayload] = Field(default_factory=list)
    experiences: list[ExperiencePayload] = Field(default_factory=list)
    education: list[EducationPayload] = Field(default_factory=list)
    projects: list[ProjectPayload] = Field(default_factory=list)
    certifications: list[CertificationPayload] = Field(default_factory=list)
    languages: list[LanguagePayload] = Field(default_factory=list)
    portfolio: list[PortfolioPayload] = Field(default_factory=list)
    references: list[ReferencePayload] = Field(default_factory=list)
    status: str = "published"
    visibility: CvVisibility = "public"
    tags: list[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    archived: bool = False


class CvUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_url: str | None = None
    fullname: str | None = Field(default=None, min_length=1, max_length=255)
    preferred_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: LocationPayload | None = None
    headline: str | None = None
    summary: str | None = None
    target_role: str | None = None
    employment_type: list[str] | None = None
    salary_expectation: str | None = None
    availability: str | None = None
    skills: list[CvSkillPayload] | None = None
    experiences: list[ExperiencePayload] | None = None
    education: list[EducationPayload] | None = None
    projects: list[ProjectPayload] | None = None
    certifications: list[CertificationPayload] | None = None
    languages: list[LanguagePayload] | None = None
    portfolio: list[PortfolioPayload] | None = None
    references: list[ReferencePayload] | None = None
    status: str | None = None
    visibility: CvVisibility | None = None
    tags: list[str] | None = None
    version: int | None = Field(default=None, ge=1)
    archived: bool | None = None


class CvResponse(BaseModel):
    id: str
    created_by: str
    avatar_url: str | None = None
    fullname: str
    preferred_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: dict[str, Any] = Field(default_factory=dict)
    headline: str | None = None
    summary: str | None = None
    target_role: str | None = None
    employment_type: list[str] = Field(default_factory=list)
    salary_expectation: str | None = None
    availability: str | None = None
    skills: list[dict[str, Any]] = Field(default_factory=list)
    experiences: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[dict[str, Any]] = Field(default_factory=list)
    portfolio: list[dict[str, Any]] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    visibility: CvVisibility = "public"
    tags: list[str] = Field(default_factory=list)
    version: int = 1
    file: dict[str, Any] = Field(default_factory=dict)
    archived: bool = False
    created_at: datetime
    updated_at: datetime


class CvExtractPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_url: str = ""
    fullname: str = ""
    preferred_name: str = ""
    email: EmailStr | str = ""
    phone: str = ""
    location: dict[str, Any] = Field(default_factory=dict)
    headline: str = ""
    summary: str = ""
    target_role: str = ""
    employment_type: list[str] = Field(default_factory=list)
    salary_expectation: str = ""
    availability: str = ""
    skills: list[dict[str, Any]] = Field(default_factory=list)
    experiences: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    languages: list[dict[str, Any]] = Field(default_factory=list)
    portfolio: list[dict[str, Any]] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"
    tags: list[str] = Field(default_factory=list)
    version: int = 1
    file: dict[str, Any] | None = None


class CvExtractResponse(BaseModel):
    extractedText: str
    cv: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class CVSearchListItem(BaseModel):
    id: str
    cv_id: str
    title: str
    fullname: str
    location: str
    location_detail: dict[str, Any] = Field(default_factory=dict)
    job_type: str
    employment_type: list[str] = Field(default_factory=list)
    working_model: str | None = None
    seniority: str | None = None
    education: str | None = None
    skills: list[str] = Field(default_factory=list)
    summary: str = ""
    experience: str = ""
    certifications: list[str] = Field(default_factory=list)
    target_role: str | None = None
    availability: str | None = None
    file: dict[str, Any] = Field(default_factory=dict)


class CVSearchListResponse(BaseModel):
    items: list[CVSearchListItem]
    total: int
    page: int
    limit: int
    totalPages: int
