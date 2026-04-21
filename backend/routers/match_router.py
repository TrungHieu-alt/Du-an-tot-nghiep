# routes/matching_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.match_service import MatchingService
from repositories.match_repo import MatchRepository
from schemas.match_schema import (
    RunMatchingResponse,
    JobMatchesResponse,
    CVMatchesResponse
)

router = APIRouter(prefix="/matching", tags=["matching"])


class RunMatchingRequest(BaseModel):
    top_k: int = 50
    min_score: float = 0.7


@router.post("/job/{job_id}/run", response_model=RunMatchingResponse)
async def run_matching_for_job(
    job_id: int,
    request: RunMatchingRequest
):
    """
    Trigger matching process for a job.
    Finds top CVs and stores match results in database.
    
    Returns:
        - job_id: ID of the job
        - total_found: Number of matches found by RAG
        - total_saved: Number of matches saved to database (>= min_score)
        - min_score: Minimum score threshold used
        - matches: Top 10 matches preview
    """
    try:
        result = await MatchingService.run_matching_for_job(
            job_id=job_id,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cv/{cv_id}/run", response_model=RunMatchingResponse)
async def run_matching_for_cv(
    cv_id: int,
    request: RunMatchingRequest
):
    """
    Trigger matching process for a CV.
    Finds top Jobs and stores match results in database.
    
    Returns:
        - cv_id: ID of the CV
        - total_found: Number of matches found by RAG
        - total_saved: Number of matches saved to database (>= min_score)
        - min_score: Minimum score threshold used
        - matches: Top 10 matches preview
    """
    try:
        result = await MatchingService.run_matching_for_cv(
            cv_id=cv_id,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/matches", response_model=JobMatchesResponse)
async def get_matches_for_job(
    job_id: int,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get stored matches for a job with enriched CV data.
    Returns CVs that match this job with scores and CV details.
    
    Enrichment happens on-the-fly, not stored in database.
    
    Returns:
        - total: Total number of matches for this job
        - matches: List of MatchWithCV (includes enriched CV data)
    """
    try:
        matches = await MatchingService.get_matches_for_job(
            job_id=job_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        total = await MatchRepository.count_by_job_id(job_id, min_score)
        
        return {
            "total": total,
            "matches": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cv/{cv_id}/matches", response_model=CVMatchesResponse)
async def get_matches_for_cv(
    cv_id: int,
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Get stored matches for a CV with enriched Job data.
    Returns Jobs that match this CV with scores and Job details.
    
    Enrichment happens on-the-fly, not stored in database.
    
    Returns:
        - total: Total number of matches for this CV
        - matches: List of MatchWithJob (includes enriched Job data)
    """
    try:
        matches = await MatchingService.get_matches_for_cv(
            cv_id=cv_id,
            min_score=min_score,
            limit=limit,
            skip=skip
        )
        
        total = await MatchRepository.count_by_cv_id(cv_id, min_score)
        
        return {
            "total": total,
            "matches": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cv/{cv_id}/matches")
async def delete_matches_for_cv(cv_id: int):
    """
    Delete all matches for a CV (cascade delete).
    Used when CV is deleted or when re-running matching.
    """
    try:
        result = await MatchingService.delete_matches_for_cv(cv_id)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/job/{job_id}/matches")
async def delete_matches_for_job(job_id: int):
    """
    Delete all matches for a Job (cascade delete).
    Used when Job is deleted or when re-running matching.
    """
    try:
        result = await MatchingService.delete_matches_for_job(job_id)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))