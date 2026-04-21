from beanie import Document
from datetime import datetime
from typing import Dict, Optional
from pymongo import IndexModel


class MatchResult(Document):
    match_id: int
    cv_id: int
    job_id: int
    score: float
    metadata: Optional[Dict] = {}  # Store matching details (cosine_ann, weighted_sim, llm_score, reason)
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "match_results"
        indexes = [
            IndexModel([("cv_id", 1), ("job_id", 1)], unique=True),
            IndexModel([("cv_id", 1), ("score", -1)]),
            IndexModel([("job_id", 1), ("score", -1)])
        ]