# models/candidate_resume.py
from beanie import Document
from datetime import datetime
from typing import List, Optional


class CandidateResume(Document):
    cv_id: int
    user_id: int
    title: str
    location: Optional[str]
    experience: Optional[str]
    skills: List[str] = []
    summary: Optional[str]
    full_text: Optional[str]
    embedding: Optional[str]
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    pdf_url: Optional[str] = None
    is_main: bool = False

    class Settings:
        name = "candidate_resumes"