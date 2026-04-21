from typing import Optional
from fastapi import HTTPException, status
from repositories.candidate_repo import CandidateRepository
from models.candidateProfile import CandidateProfile
from typing import List


class CandidateService:
    @staticmethod
    async def create_profile(user_id: int, full_name: str, location: Optional[str],
                            experience_years: int, skills: list, summary: Optional[str]) -> CandidateProfile:
        existing = await CandidateRepository.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate profile already exists",
            )
        return await CandidateRepository.create(user_id, full_name, location, experience_years, skills, summary)

    @staticmethod
    async def get_profile(user_id: int) -> Optional[CandidateProfile]:
        profile = await CandidateRepository.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )
        return profile

    @staticmethod
    async def update_profile(user_id: int, **kwargs) -> Optional[CandidateProfile]:
        profile = await CandidateRepository.update(user_id, **kwargs)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )
        return profile

    @staticmethod
    async def get_all_profiles() -> List[CandidateProfile]:
        return await CandidateRepository.get_all()