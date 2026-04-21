from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class RecruiterProfileRequest(BaseModel):
    company_name: str
    recruiter_title: str
    company_logo: Optional[str] = None
    about_company: Optional[str] = None
    hiring_fields: List[str] = []


class RecruiterProfileResponse(BaseModel):
    user_id: int
    company_name: str
    recruiter_title: str
    company_logo: Optional[str]
    about_company: Optional[str]
    hiring_fields: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True