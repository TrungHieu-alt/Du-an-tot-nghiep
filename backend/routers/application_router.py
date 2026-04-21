# routes/application_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


class CreateApplicationRequest(BaseModel):
    job_id: int = Field(..., gt=0, description="Job ID to apply for")
    candidate_id: int = Field(..., gt=0, description="Candidate ID applying")
    cv_id: int = Field(..., gt=0, description="CV ID to submit")
    cover_letter: str = Field(
        default="",
        max_length=5000,
        description="Optional cover letter (max 5000 characters)"
    )


class UpdateApplicationStatusRequest(BaseModel):
    status: str = Field(
        ...,
        description="Application status (pending, viewed, interviewing, rejected, hired)"
    )


@router.post("/")
async def create_application(request: CreateApplicationRequest):
    """
    Create new application.
    Candidate applies to a job with their CV and optional cover letter.
    
    Returns:
        Application details with ID and current status
    """
    try:
        result = await ApplicationService.create_application(
            job_id=request.job_id,
            candidate_id=request.candidate_id,
            cv_id=request.cv_id,
            cover_letter=request.cover_letter
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_applications_for_job(
    job_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get applications for a job.
    Recruiter can see all applications for their job with optional filtering.
    
    Query Parameters:
        status: Optional status filter (pending, viewed, interviewing, rejected, hired)
        limit: Results per page (1-100, default 50)
        skip: Pagination offset (default 0)
    
    Returns:
        Paginated list of applications with total count
    """
    try:
        result = await ApplicationService.get_applications_for_job(
            job_id=job_id,
            status=status,
            limit=limit,
            skip=skip
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/{candidate_id}")
async def get_applications_for_candidate(
    candidate_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get applications submitted by a candidate.
    Candidate can see their own applications with optional filtering.
    
    Query Parameters:
        status: Optional status filter (pending, viewed, interviewing, rejected, hired)
        limit: Results per page (1-100, default 50)
        skip: Pagination offset (default 0)
    
    Returns:
        Paginated list of applications with total count
    """
    try:
        result = await ApplicationService.get_applications_for_candidate(
            candidate_id=candidate_id,
            status=status,
            limit=limit,
            skip=skip
        )
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{app_id}/status")
async def update_application_status(
    app_id: int,
    request: UpdateApplicationStatusRequest = None
):
    """
    Update application status.
    Recruiter can update status (pending, viewed, interviewing, rejected, hired).
    
    Valid statuses:
        - pending: Initial state
        - viewed: Recruiter reviewed the application
        - interviewing: Candidate is in interview process
        - rejected: Application was rejected
        - hired: Candidate was hired
    
    Returns:
        Updated application with new status and timestamp
    """
    try:
        result = await ApplicationService.update_application_status(
            app_id=app_id,
            status=request.status
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{app_id}")
async def delete_application(
    app_id: int
):
    """
    Delete an application.
    
    Returns:
        Success message
    """
    try:
        result = await ApplicationService.delete_application(app_id)
        
        return {
            "success": True,
            "message": "Application deleted successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))