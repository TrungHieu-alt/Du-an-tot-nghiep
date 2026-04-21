from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CandidateProfileRequest(BaseModel):
    full_name: str
    location: Optional[str] = None
    experience_years: int = 0
    skills: List[str] = []
    summary: Optional[str] = None


class CandidateProfileResponse(BaseModel):
    user_id: int
    full_name: str
    location: Optional[str]
    experience_years: int
    skills: List[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True