# models/candidate_profile.py
from beanie import Document
from datetime import datetime
from typing import List, Optional


class CandidateProfile(Document):
    user_id: int
    full_name: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    skills: List[str] = []
    summary: Optional[str] = None

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "candidate_profiles"