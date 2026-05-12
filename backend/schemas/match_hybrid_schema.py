from typing import Optional

from pydantic import BaseModel, Field


class RunMatchingHybridRequest(BaseModel):
    top_k: int = Field(default=10, ge=1, le=10)
    min_score: float = Field(default=0.0, ge=0.0, le=100.0)
    include_failed: bool = False
    strict_filters: bool = True


class SkippedGroup(BaseModel):
    group: str
    reason: str


class FailedFilter(BaseModel):
    field: str
    reason: str


class HybridBreakdown(BaseModel):
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


class MatchHybridItem(BaseModel):
    rank: int
    job_id: int
    cv_id: int
    final_score: float
    passed: bool
    failed_filters: list[FailedFilter]
    breakdown: HybridBreakdown
    skipped_groups: list[SkippedGroup]
    warnings: list[str]
    explanations: dict[str, str]


class RunMatchingHybridResponse(BaseModel):
    anchor_type: str
    anchor_id: int
    total_candidates: int
    total_after_filter: int
    total_returned: int
    runtime_ms_total: float
    runtime_ms_filter: float
    runtime_ms_scoring: float
    runtime_ms_sort: float
    matches: list[MatchHybridItem]


class ErrorDetailResponse(BaseModel):
    detail: str
