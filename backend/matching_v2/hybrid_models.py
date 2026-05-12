"""Dataclasses for the additive hybrid Matching V2 endpoint.

These models are intentionally separate from `models.py` so the existing
`/api/v2/prototype/matching/*` response contract remains unchanged.
Scores in this module use the 0..100 scale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SkippedGroup:
    group: str
    reason: str


@dataclass(frozen=True)
class FailedFilter:
    field: str
    reason: str


@dataclass
class HybridBreakdown:
    title_score: Optional[float] = None
    skills_score: Optional[float] = None
    experience_score: Optional[float] = None
    project_score: Optional[float] = None
    seniority_score: Optional[float] = None
    education_score: Optional[float] = None
    certification_score: Optional[float] = None
    language_score: Optional[float] = None
    location_score: Optional[float] = None
    salary_score: Optional[float] = None
    job_type_score: Optional[float] = None


@dataclass(frozen=True)
class WeightedGroupScore:
    group: str
    score: float
    weight: float


@dataclass
class HybridPairResult:
    job_id: int
    cv_id: int
    final_score: float
    passed: bool
    breakdown: HybridBreakdown
    skipped_groups: list[SkippedGroup] = field(default_factory=list)
    failed_filters: list[FailedFilter] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    explanations: dict[str, str] = field(default_factory=dict)


@dataclass
class MatchHybridItem(HybridPairResult):
    rank: int = 0


@dataclass
class RunMatchingHybridResponse:
    anchor_type: str
    anchor_id: int
    total_candidates: int
    total_after_filter: int
    total_returned: int
    runtime_ms_total: float
    runtime_ms_filter: float
    runtime_ms_scoring: float
    runtime_ms_sort: float
    matches: list[MatchHybridItem] = field(default_factory=list)
