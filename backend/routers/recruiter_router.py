from fastapi import APIRouter, status
from schemas.recruiter_schema import RecruiterProfileRequest, RecruiterProfileResponse
from services.recruiter_service import RecruiterService

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.post("/profile/{user_id}", status_code=status.HTTP_201_CREATED, response_model=RecruiterProfileResponse)
async def create_profile(user_id: int, req: RecruiterProfileRequest):
    profile = await RecruiterService.create_profile(
        user_id, req.company_name, req.recruiter_title, req.company_logo,
        req.about_company, req.hiring_fields
    )
    return profile


@router.get("/profile/{user_id}", response_model=RecruiterProfileResponse)
async def get_profile(user_id: int):
    return await RecruiterService.get_profile(user_id)


@router.put("/profile/{user_id}", response_model=RecruiterProfileResponse)
async def update_profile(user_id: int, req: RecruiterProfileRequest):
    profile = await RecruiterService.update_profile(
        user_id,
        company_name=req.company_name,
        recruiter_title=req.recruiter_title,
        company_logo=req.company_logo,
        about_company=req.about_company,
        hiring_fields=req.hiring_fields,
    )
    return profile