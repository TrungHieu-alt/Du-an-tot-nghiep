from typing import Optional
from fastapi import HTTPException, status
from repositories.recruiter_repo import RecruiterRepository
from models.recruiterProfile import RecruiterProfile


class RecruiterService:
    @staticmethod
    async def create_profile(user_id: int, company_name: str, recruiter_title: str,
                            company_logo: Optional[str], about_company: Optional[str],
                            hiring_fields: list) -> RecruiterProfile:
        existing = await RecruiterRepository.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recruiter profile already exists",
            )
        return await RecruiterRepository.create(user_id, company_name, recruiter_title, company_logo, about_company, hiring_fields)

    @staticmethod
    async def get_profile(user_id: int) -> Optional[RecruiterProfile]:
        profile = await RecruiterRepository.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter profile not found",
            )
        return profile

    @staticmethod
    async def update_profile(user_id: int, **kwargs) -> Optional[RecruiterProfile]:
        profile = await RecruiterRepository.update(user_id, **kwargs)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter profile not found",
            )
        return profile