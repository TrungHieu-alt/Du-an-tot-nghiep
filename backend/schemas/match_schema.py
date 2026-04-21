from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime


# ==================== Base Match Result ====================
class MatchResultBase(BaseModel):
    match_id: int
    cv_id: int
    job_id: int
    score: float
    metadata: Dict = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Enriched Responses ====================

# CV Summary for Job Matches
class CVSummary(BaseModel):
    title: str
    location: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []
    user_id: int


# Job Summary for CV Matches
class JobSummary(BaseModel):
    title: str
    role: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    skills: List[str] = []
    recruiter_id: int


# Match with CV details (for recruiters viewing job matches)
class MatchWithCV(BaseModel):
    match_id: int
    cv_id: int
    score: float
    metadata: Dict
    created_at: datetime
    updated_at: datetime
    cv: CVSummary  # Enriched on-the-fly


# Match with Job details (for candidates viewing CV matches)
class MatchWithJob(BaseModel):
    match_id: int
    job_id: int
    score: float
    metadata: Dict
    created_at: datetime
    updated_at: datetime
    job: JobSummary  # Enriched on-the-fly


# ==================== List Responses ====================
class JobMatchesResponse(BaseModel):
    total: int
    matches: List[MatchWithCV]


class CVMatchesResponse(BaseModel):
    total: int
    matches: List[MatchWithJob]


# ==================== Run Matching Responses ====================
class MatchSummary(BaseModel):
    match_id: int
    cv_id: Optional[int] = None
    job_id: Optional[int] = None
    score: float
    reason: str


class RunMatchingResponse(BaseModel):
    cv_id: Optional[int] = None
    job_id: Optional[int] = None
    total_found: int
    total_saved: int
    min_score: float
    matches: List[MatchSummary]  # Top 10 preview