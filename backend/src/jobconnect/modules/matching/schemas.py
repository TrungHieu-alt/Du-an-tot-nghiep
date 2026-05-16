from __future__ import annotations

from pydantic import Field

from jobconnect.modules.api.shared import APIModel
from jobconnect.modules.jobs.schemas import JobSummary
from jobconnect.modules.resumes.schemas import ResumeSummary


class SemanticSearchRequest(APIModel):
    query: str
    top_k: int = Field(default=20, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)


class MatchingRequest(APIModel):
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.7, ge=0.0, le=1.0)
    rerank: bool = False


class MatchingScoreBreakdown(APIModel):
    title_sim: float
    skills_sim: float
    req_exp_sim: float
    req_summary_sim: float
    bonus_exact_skill: float = 0.0
    penalty_missing_required: float = 0.0


class MatchingRuntime(APIModel):
    total_ms: float
    retrieval_ms: float
    filter_ms: float
    scoring_ms: float
    rerank_ms: float
    candidates_total: int
    candidates_after_filter: int
    rerank_applied: bool
    warnings: list[str] = Field(default_factory=list)


class MatchingItem(APIModel):
    rank: int
    resume: ResumeSummary | None = None
    job: JobSummary | None = None
    final_score: float
    score_breakdown: MatchingScoreBreakdown
    exact_skill_overlap: list[str] = Field(default_factory=list)
    hard_filter_notes: list[str] = Field(default_factory=list)
    missing_embedding_notes: list[str] = Field(default_factory=list)
    reasoning: str


class MatchingResponse(APIModel):
    anchor: dict
    items: list[MatchingItem]
    runtime: MatchingRuntime
