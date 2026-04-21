from typing import Optional, List
from models.candidateProfile import CandidateProfile


class CandidateRepository:
    @staticmethod
    async def create(user_id: int, full_name: str, location: Optional[str], 
                    experience_years: int, skills: list, summary: Optional[str]) -> CandidateProfile:
        profile = CandidateProfile(
            user_id=user_id,
            full_name=full_name,
            location=location,
            experience_years=experience_years,
            skills=skills,
            summary=summary,
        )
        await profile.insert()
        return profile

    @staticmethod
    async def get_by_user_id(user_id: int) -> Optional[CandidateProfile]:
        return await CandidateProfile.find_one(CandidateProfile.user_id == user_id)

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[CandidateProfile]:
        """Alias for get_by_user_id for compatibility"""
        return await CandidateProfile.find_one(CandidateProfile.user_id == user_id)

    @staticmethod
    async def update(user_id: int, **kwargs) -> Optional[CandidateProfile]:
        profile = await CandidateProfile.find_one(CandidateProfile.user_id == user_id)
        if profile:
            await profile.update({"$set": kwargs})
            return await CandidateRepository.get_by_user_id(user_id)
        return None

    @staticmethod
    async def delete(user_id: int) -> bool:
        profile = await CandidateProfile.find_one(CandidateProfile.user_id == user_id)
        if profile:
            await profile.delete()
            return True
        return False

    @staticmethod
    async def get_all() -> List[CandidateProfile]:
        return await CandidateProfile.find().to_list()