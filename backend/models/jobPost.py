# models/job_post.py
from beanie import Document
from datetime import datetime
from typing import List, Optional


class JobPost(Document):
    job_id: int
    recruiter_id: int
    title: str
    role: str
    location: str
    job_type: str
    experience_level: str
    skills: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    full_text: Optional[str] = None
    embedding: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    pdf_url: Optional[str] = None

    class Settings:
        name = "job_posts"