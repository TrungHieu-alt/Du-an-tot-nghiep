from fastapi import APIRouter, status, UploadFile, File, Form, Query
from typing import List, Dict
from schemas.cv_schema import CandidateResumeRequest, CandidateResumeResponse
from services.cv_service import CVService

router = APIRouter(prefix="/cv", tags=["cv"])


# ============================
# CREATE CV (manual JSON)
# ============================
@router.post("/create/{user_id}", status_code=status.HTTP_201_CREATED, response_model=CandidateResumeResponse)
async def create_cv(user_id: int, req: CandidateResumeRequest):
    """
    Create CV manually with provided data (no parsing).
    Use this when you have structured CV data.
    """
    cv = await CVService.create_cv(
        user_id=user_id,
        title=req.title,
        location=req.location,
        experience=req.experience,
        skills=req.skills,
        summary=req.summary,
        full_text=req.full_text,
        pdf_url=req.pdf_url,
        is_main=req.is_main
    )
    return cv


# ============================
# UPLOAD CV FILE (with auto parsing & embedding)
# ============================
@router.post("/upload/{user_id}", response_model=CandidateResumeResponse)
async def upload_cv(
    user_id: int,
    file: UploadFile = File(...),
    is_main: bool = Form(False)
):
    """
    Upload CV from file (PDF or text).
    Automatically parses content and generates embeddings.
    """
    return await CVService.upload_file(user_id, file, is_main)


@router.post("/upload-text/{user_id}", response_model=CandidateResumeResponse)
async def upload_cv_text(
    user_id: int,
    full_text: str = Form(...),
    title: str = Form(None),
    is_main: bool = Form(False)
):
    """
    Upload CV from plain text.
    Automatically parses content and generates embeddings.
    """
    return await CVService.upload_cv_from_text(user_id, full_text, title, is_main=is_main)


# ============================
# GET CV
# ============================
@router.get("/{cv_id}", response_model=CandidateResumeResponse)
async def get_cv(cv_id: int):
    """Get single CV by ID"""
    return await CVService.get_cv(cv_id)


@router.get("/user/{user_id}", response_model=List[CandidateResumeResponse])
async def get_user_cvs(user_id: int):
    """Get all CVs for a specific user"""
    return await CVService.get_user_cvs(user_id)


@router.get("/main/user/{user_id}", response_model=CandidateResumeResponse)
async def get_main_cv(user_id: int):
    """Get the main/primary CV of a user"""
    return await CVService.get_main_cv(user_id)


# ============================
# UPDATE CV
# ============================
@router.put("/{cv_id}", response_model=CandidateResumeResponse)
async def update_cv(cv_id: int, req: CandidateResumeRequest):
    """Update CV details"""
    cv = await CVService.update_cv(
        cv_id,
        title=req.title,
        location=req.location,
        experience=req.experience,
        skills=req.skills,
        summary=req.summary,
        full_text=req.full_text,
        pdf_url=req.pdf_url,
        is_main=req.is_main,
    )
    return cv


# ============================
# DELETE CV
# ============================
@router.delete("/{cv_id}", status_code=status.HTTP_200_OK)
async def delete_cv(cv_id: int):
    """Delete CV (removes from both MongoDB and ChromaDB)"""
    await CVService.delete_cv(cv_id)
    return {"message": "CV deleted successfully"}


# ============================
# MATCHING Operations
# ============================
@router.get("/match/{cv_id}/jobs", response_model=List[Dict])
async def find_matching_jobs(cv_id: int, top_k: int = Query(5, ge=1, le=20)):
    """
    Find top-K matching jobs for a CV using vector similarity.
    
    Args:
        cv_id: CV ID
        top_k: Number of top matches (1-20, default: 5)
    """
    return CVService.find_matching_jobs(cv_id, top_k)


@router.get("/match/{cv_id}/jobs/{job_id}", response_model=Dict)
async def get_cv_job_match(cv_id: int, job_id: int):
    """
    Get detailed match score between a CV and a specific Job.
    
    Args:
        cv_id: CV ID
        job_id: Job ID
    """
    return CVService.calculate_cv_jd_match(cv_id, job_id)