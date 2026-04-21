from typing import Optional
from models.recruiterProfile import RecruiterProfile


class RecruiterRepository:
    @staticmethod
    async def create(user_id: int, company_name: str, recruiter_title: str,
                    company_logo: Optional[str], about_company: Optional[str],
                    hiring_fields: list) -> RecruiterProfile:
        profile = RecruiterProfile(
            user_id=user_id,
            company_name=company_name,
            recruiter_title=recruiter_title,
            company_logo=company_logo,
            about_company=about_company,
            hiring_fields=hiring_fields,
        )
        await profile.insert()
        return profile

    @staticmethod
    async def get_by_user_id(user_id: int) -> Optional[RecruiterProfile]:
        return await RecruiterProfile.find_one(RecruiterProfile.user_id == user_id)

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[RecruiterProfile]:
        """Alias for get_by_user_id for compatibility"""
        return await RecruiterProfile.find_one(RecruiterProfile.user_id == user_id)

    @staticmethod
    async def update(user_id: int, **kwargs) -> Optional[RecruiterProfile]:
        profile = await RecruiterProfile.find_one(RecruiterProfile.user_id == user_id)
        if profile:
            await profile.update({"$set": kwargs})
            return await RecruiterRepository.get_by_user_id(user_id)
        return None

    @staticmethod
    async def delete(user_id: int) -> bool:
        profile = await RecruiterProfile.find_one(RecruiterProfile.user_id == user_id)
        if profile:
            await profile.delete()
            return True
        return False