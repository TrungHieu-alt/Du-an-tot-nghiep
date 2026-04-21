from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class JobPostRequest(BaseModel):
    title: str
    role: str
    location: str
    job_type: str
    experience_level: str
    skills: List[str] = []
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    full_text: Optional[str] = None
    pdf_url: Optional[str] = None


class JobPostResponse(BaseModel):
    job_id: int
    recruiter_id: int
    title: str
    role: str
    location: str
    job_type: str
    experience_level: str
    skills: List[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    full_text: Optional[str]
    pdf_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True