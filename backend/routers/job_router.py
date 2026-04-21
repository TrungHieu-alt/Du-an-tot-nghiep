from fastapi import APIRouter, status, UploadFile, File, Form, Query
from typing import List, Dict
from schemas.job_schema import JobPostRequest, JobPostResponse
from services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ============================
# CREATE JOB (manual JSON)
# ============================
@router.post("/create/{recruiter_id}", status_code=status.HTTP_201_CREATED, response_model=JobPostResponse)
async def create_job(recruiter_id: int, req: JobPostRequest):
    """
    Create job posting manually with provided data (no parsing).
    Use this when you have structured job data.
    """
    job = await JobService.create_job(
        recruiter_id, req.title, req.role, req.location, req.job_type,
        req.experience_level, req.skills, req.salary_min, req.salary_max, req.full_text, req.pdf_url
    )
    return job


# ============================
# UPLOAD JOB FILE (with auto parsing & embedding)
# ============================
@router.post("/upload/{recruiter_id}", response_model=JobPostResponse)
async def upload_job(
    recruiter_id: int,
    file: UploadFile = File(...),
    title: str = Form(None),
    role: str = Form(None),
    location: str = Form(None),
    job_type: str = Form(None),
    experience_level: str = Form(None),
    salary_min: float = Form(None),
    salary_max: float = Form(None),
):
    """
    Upload job posting from file (PDF or text).
    Automatically parses content and generates embeddings.
    Optional fields override parsed values if provided.
    """
    return await JobService.upload_file(
        recruiter_id, file, title, role, location,
        job_type, experience_level, salary_min, salary_max
    )


@router.post("/upload-text/{recruiter_id}", response_model=JobPostResponse)
async def upload_job_text(
    recruiter_id: int,
    full_text: str = Form(...),
    title: str = Form(None),
    role: str = Form(None),
    location: str = Form(None),
    job_type: str = Form(None),
    experience_level: str = Form(None),
    salary_min: float = Form(None),
    salary_max: float = Form(None),
):
    """
    Upload job posting from plain text.
    Automatically parses content and generates embeddings.
    Optional fields override parsed values if provided.
    """
    return await JobService.upload_job_from_text(
        recruiter_id, full_text, title, role, location,
        job_type, experience_level, salary_min, salary_max
    )


# ============================
# GET JOB
# ============================
@router.get("", response_model=List[JobPostResponse])
async def get_all_jobs():
    """Get all job postings"""
    return await JobService.get_all_jobs()


@router.get("/{job_id}", response_model=JobPostResponse)
async def get_job(job_id: int):
    """Get single job posting by ID"""
    return await JobService.get_job(job_id)


@router.get("/recruiter/{recruiter_id}", response_model=List[JobPostResponse])
async def get_recruiter_jobs(recruiter_id: int):
    """Get all job postings from a specific recruiter"""
    return await JobService.get_recruiter_jobs(recruiter_id)


# ============================
# UPDATE JOB
# ============================
@router.put("/{job_id}", response_model=JobPostResponse)
async def update_job(job_id: int, req: JobPostRequest):
    """Update job posting details"""
    job = await JobService.update_job(
        job_id,
        title=req.title,
        role=req.role,
        location=req.location,
        job_type=req.job_type,
        experience_level=req.experience_level,
        skills=req.skills,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        full_text=req.full_text,
        pdf_url=req.pdf_url,
    )
    return job


# ============================
# DELETE JOB
# ============================
@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(job_id: int):
    """Delete job posting (removes from both MongoDB and ChromaDB)"""
    await JobService.delete_job(job_id)
    return {"message": "Job deleted successfully"}


# ============================
# MATCHING Operations
# ============================
@router.get("/match/{job_id}/cvs", response_model=List[Dict])
async def find_matching_cvs(job_id: int, top_k: int = Query(5, ge=1, le=20)):
    """
    Find top-K matching CVs for a job posting using vector similarity.
    
    Args:
        job_id: Job ID
        top_k: Number of top matches (1-20, default: 5)
    """
    return JobService.find_matching_cvs(job_id, top_k)


@router.get("/match/{job_id}/cvs/{cv_id}", response_model=Dict)
async def get_job_cv_match(job_id: int, cv_id: int):
    """
    Get detailed match score between a job posting and a specific CV.
    
    Args:
        job_id: Job ID
        cv_id: CV ID
    """
    return JobService.calculate_jd_cv_match(job_id, cv_id)