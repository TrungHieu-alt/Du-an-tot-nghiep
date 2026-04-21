from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CandidateResumeRequest(BaseModel):
    title: str
    location: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []
    summary: Optional[str] = None
    full_text: Optional[str] = None
    pdf_url: Optional[str] = None
    is_main: bool = False


class CandidateResumeResponse(BaseModel):
    cv_id: int
    user_id: int
    title: str
    location: Optional[str]
    experience: Optional[str]
    skills: List[str]
    summary: Optional[str]
    full_text: Optional[str]
    pdf_url: Optional[str]
    is_main: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True