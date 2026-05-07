"""Immutable data models for the Matching V2 run-only prototype.

All types are plain dataclasses — no ORM, no persistence.
Source of truth: docs/REQUIREMENTS.md §5, §9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Entity models (mirror PostgreSQL tables — read-only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateProfileV2:
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
class JobPostV2:
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
class CandidateEmbeddingsV2:
    cv_id: int
    emb_title: Optional[list[float]]
    emb_skills: Optional[list[float]]
    emb_summary: Optional[list[float]]
    emb_experience: Optional[list[float]]


@dataclass(frozen=True)
class JobEmbeddingsV2:
    job_id: int
    emb_title: Optional[list[float]]
    emb_skills: Optional[list[float]]
    emb_requirement: Optional[list[float]]


# ---------------------------------------------------------------------------
# Output models (run result — never persisted)
# ---------------------------------------------------------------------------

@dataclass
class MatchItemV2:
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
class RunMatchingV2Response:
    anchor_type: str           # "job" | "cv"
    anchor_id: int
    total_candidates: int      # opposite-side count before filters
    total_after_filter: int    # count after hard filters
    total_returned: int        # count after min_score + top_k
    runtime_ms_total: float
    runtime_ms_filter: float
    runtime_ms_scoring: float
    runtime_ms_sort: float
    matches: list[MatchItemV2] = field(default_factory=list)
