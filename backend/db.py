# db.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.user import User
from models.candidateProfile import CandidateProfile
from models.recruiterProfile import RecruiterProfile
from models.jobPost import JobPost
from models.candidateResume import CandidateResume
from models.matchResult import MatchResult
from models.application import Application

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "job_matching"


async def init_db():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    await init_beanie(
        database=db,
        document_models=[
            User,
            CandidateProfile,
            RecruiterProfile,
            JobPost,
            CandidateResume,
            MatchResult,
            Application,
        ],
    )
