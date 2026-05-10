"""Pydantic schemas for the V2 catalog read-only endpoints.

Source of truth for the underlying tables: backend/db_v2/orm_models.py.
These models are response-only; the runtime path uses psycopg directly and
does NOT import the ORM module to keep the matching_v2 scope-lock intact.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------

class JobV2ListItem(BaseModel):
    job_id: int
    title: str
    location: str
    job_type: str
    seniority: str
    skills: list[str] = Field(default_factory=list)


class JobV2Detail(BaseModel):
    job_id: int
    title: str
    skills: list[str] = Field(default_factory=list)
    requirement: str
    location: str
    job_type: str
    seniority: str
    education: str
    required_certifications: list[str] = Field(default_factory=list)


class JobV2ListResponse(BaseModel):
    items: list[JobV2ListItem]
    total: int


# ---------------------------------------------------------------------------
# Candidate (CV)
# ---------------------------------------------------------------------------

class CVV2ListItem(BaseModel):
    cv_id: int
    title: str
    location: str
    job_type: str
    seniority: str
    skills: list[str] = Field(default_factory=list)


class CVV2Detail(BaseModel):
    cv_id: int
    title: str
    skills: list[str] = Field(default_factory=list)
    summary: str
    experience: str
    location: str
    job_type: str
    seniority: str
    education: str
    certifications: list[str] = Field(default_factory=list)


class CVV2ListResponse(BaseModel):
    items: list[CVV2ListItem]
    total: int


# ---------------------------------------------------------------------------
# Search (semantic, pgvector-backed)
# ---------------------------------------------------------------------------

class CatalogSearchRequest(BaseModel):
    """Body for POST /v2/prototype/catalog/{jobs|cvs}/search.

    Fields:
        q: free-form query (1..200 chars). Empty string is rejected by
           Pydantic; the endpoint additionally short-circuits when the
           trimmed query is empty (returns items=[], total=0 without
           hitting the database).
        top_k: max items to return (1..50, default 20).
        blend_skills: weight given to skills-similarity in the blend
                      score = (1 - blend) * sim_title + blend * sim_skills.
                      Default 0.3 — title carries more weight by default.
    """

    q: str = Field(min_length=1, max_length=200)
    top_k: int = Field(default=20, ge=1, le=50)
    blend_skills: float = Field(default=0.3, ge=0.0, le=1.0)


class JobSearchItem(JobV2ListItem):
    score: float


class CVSearchItem(CVV2ListItem):
    score: float


class JobSearchResponse(BaseModel):
    items: list[JobSearchItem]
    total: int


class CVSearchResponse(BaseModel):
    items: list[CVSearchItem]
    total: int


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class CatalogErrorResponse(BaseModel):
    detail: str
