# models/recruiter_profile.py
from beanie import Document
from datetime import datetime
from typing import List, Optional


class RecruiterProfile(Document):
    user_id: int
    company_name: Optional[str]
    recruiter_title: Optional[str]
    company_logo: Optional[str]
    about_company: Optional[str]
    hiring_fields: List[str] = []

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "recruiter_profiles"