from pydantic import BaseModel, Field


class RunMatchingV2Request(BaseModel):
    top_k: int = Field(default=10)
    min_score: float = Field(default=0.7)


class MatchItemV2Response(BaseModel):
    rank: int
    cv_id: int
    job_id: int
    final_score: float
    title_score: float
    skills_score: float
    req_exp_score: float
    req_summary_score: float
    reasoning: str


class RunMatchingV2Response(BaseModel):
    anchor_type: str
    anchor_id: int
    total_candidates: int
    total_after_filter: int
    total_returned: int
    runtime_ms_total: float
    runtime_ms_filter: float
    runtime_ms_scoring: float
    runtime_ms_sort: float
    matches: list[MatchItemV2Response]
