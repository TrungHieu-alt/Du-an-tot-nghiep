from fastapi import APIRouter, status
from schemas.candidate_schema import CandidateProfileRequest, CandidateProfileResponse
from services.candidate_service import CandidateService
from typing import List

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.post("/profile/{user_id}", status_code=status.HTTP_201_CREATED, response_model=CandidateProfileResponse)
async def create_profile(user_id: int, req: CandidateProfileRequest):
    profile = await CandidateService.create_profile(
        user_id, req.full_name, req.location, req.experience_years, req.skills, req.summary
    )
    return profile


@router.get("/profile/{user_id}", response_model=CandidateProfileResponse)
async def get_profile(user_id: int):
    return await CandidateService.get_profile(user_id)


@router.put("/profile/{user_id}", response_model=CandidateProfileResponse)
async def update_profile(user_id: int, req: CandidateProfileRequest):
    profile = await CandidateService.update_profile(
        user_id,
        full_name=req.full_name,
        location=req.location,
        experience_years=req.experience_years,
        skills=req.skills,
        summary=req.summary,
    )
    return profile


@router.get("/profiles", response_model=List[CandidateProfileResponse])
async def get_all_candidate_profiles():
    return await CandidateService.get_all_profiles()