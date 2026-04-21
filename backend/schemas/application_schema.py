# schemas/application_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


class ApplicationRequest(BaseModel):
    """Schema for creating a new application"""
    job_id: int = Field(..., gt=0, description="Job ID to apply for")
    cv_id: int = Field(..., gt=0, description="CV ID to submit")
    cover_letter: str = Field(
        default="",
        max_length=5000,
        description="Optional cover letter"
    )


class ApplicationUpdateRequest(BaseModel):
    """Schema for updating application status"""
    status: Literal["pending", "viewed", "interviewing", "rejected", "hired"] = Field(
        ...,
        description="Application status"
    )


class ApplicationResponse(BaseModel):
    """Schema for application response"""
    app_id: int
    job_id: int
    candidate_id: int
    cv_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Schema for paginated application list response"""
    total: int = Field(..., ge=0, description="Total number of applications")
    limit: int = Field(..., gt=0, description="Results per page")
    skip: int = Field(..., ge=0, description="Number of results skipped")
    applications: list = Field(..., description="List of applications")

    class Config:
        from_attributes = True