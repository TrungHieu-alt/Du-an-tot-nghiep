# models/user.py
from beanie import Document
from datetime import datetime
from typing import Literal, Optional


class User(Document):
    user_id: int
    email: str
    password_hash: str
    role: Optional[Literal["candidate", "recruiter"]] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    class Settings:
        name = "users"