# models/application.py
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Literal, Optional


class Application(Document):
    app_id: int
    job_id: int
    candidate_id: int
    cv_id: int
    match_id: Optional[int] = None
    cover_letter: str = Field(default="", max_length=5000)
    status: Literal["pending", "viewed", "interviewing", "rejected", "hired"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "applications"