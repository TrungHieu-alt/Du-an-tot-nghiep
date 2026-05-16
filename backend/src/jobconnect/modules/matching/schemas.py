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
    top_k: int = Field(default=20, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rerank: bool = False


class MatchingScoreBreakdown(APIModel):
    title_sim: float
    skills_sim: float
    req_exp_sim: float
    req_summary_sim: float


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
    runtime: dict
