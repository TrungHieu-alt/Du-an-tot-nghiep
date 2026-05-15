"""Immutable matching data models used by the production matching module.

All types are plain dataclasses — no ORM, no persistence.
Source of truth: docs/REQUIREMENTS.md and production matching HLD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Entity models (mirror PostgreSQL rows — read-only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateProfileMatch:
    cv_id: int
    title: str
    skills: tuple[str, ...]
    summary: str
    experience: str
    location: str
    job_type: str
    seniority: str
    education: str
    certifications: tuple[str, ...]


@dataclass(frozen=True)
class JobPostMatch:
    job_id: int
    title: str
    skills: tuple[str, ...]
    requirement: str
    location: str
    job_type: str
    seniority: str
    education: str
    required_certifications: tuple[str, ...]


@dataclass(frozen=True)
class CandidateEmbeddings:
    cv_id: int
    emb_title: Optional[list[float]]
    emb_skills: Optional[list[float]]
    emb_summary: Optional[list[float]]
    emb_experience: Optional[list[float]]


@dataclass(frozen=True)
class JobEmbeddings:
    job_id: int
    emb_title: Optional[list[float]]
    emb_skills: Optional[list[float]]
    emb_requirement: Optional[list[float]]


# ---------------------------------------------------------------------------
# Output models (run result — never persisted)
# ---------------------------------------------------------------------------

@dataclass
class MatchItem:
    rank: int
    cv_id: int
    job_id: int
    final_score: float
    title_score: float
    skills_score: float
    req_exp_score: float
    req_summary_score: float
    reasoning: str


@dataclass
class RunMatchingResponse:
    anchor_type: str           # "job" | "cv"
    anchor_id: int
    total_candidates: int      # opposite-side count before filters
    total_after_filter: int    # count after hard filters
    total_returned: int        # count after min_score + top_k
    runtime_ms_total: float
    runtime_ms_filter: float
    runtime_ms_scoring: float
    runtime_ms_sort: float
    matches: list[MatchItem] = field(default_factory=list)
