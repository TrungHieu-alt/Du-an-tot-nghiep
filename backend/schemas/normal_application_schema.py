"""Schemas for normal job applications.

Applications connect normal PostgreSQL Jobs and CVs. They are separate from
Matching V2 and intentionally contain no scoring fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ApplicationStatus = Literal[
    "submitted",
    "reviewing",
    "shortlisted",
    "rejected",
    "accepted",
    "withdrawn",
]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jobId: UUID
    cvId: UUID
    coverLetter: str | None = Field(default=None, max_length=5000)


class ApplicationUpdateStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApplicationStatus


class ApplicationJobSummary(BaseModel):
    id: UUID
    title: str
    companyName: str | None = None


class ApplicationCvSummary(BaseModel):
    id: UUID
    fullname: str
    headline: str | None = None


class ApplicationUserSummary(BaseModel):
    id: UUID
    email: str
    fullName: str | None = None
    role: str


class ApplicationOut(BaseModel):
    id: UUID
    jobId: UUID
    cvId: UUID
    candidateId: UUID
    recruiterId: UUID
    status: ApplicationStatus
    coverLetter: str | None = None
    createdAt: datetime
    updatedAt: datetime
    job: ApplicationJobSummary
    cv: ApplicationCvSummary
    candidate: ApplicationUserSummary | None = None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationOut]
    total: int
    page: int
    limit: int
    totalPages: int
    pagination: dict[str, int] = Field(default_factory=dict)
