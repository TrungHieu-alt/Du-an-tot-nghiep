"""Compatibility aliases for normal search.

The canonical normal Job search endpoint is now `GET /api/job/search`.
These aliases keep the existing frontend/test surface (`/api/jobs`, `/api/cvs`,
`/api/candidates`) stable while routing to normal PostgreSQL Job/CV tables.
They do not read V2 prototype tables.
"""

from __future__ import annotations

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, Query

from routers.auth import get_db_connection
from routers.cv_router import search_cvs_response
from routers.job_router import search_jobs_response
from schemas.normal_cv_schema import CVSearchListResponse
from schemas.normal_job_schema import JobSearchListResponse


router = APIRouter(tags=["normal-search"])
DbConnection = Annotated[psycopg.Connection, Depends(get_db_connection)]


@router.get("/jobs", response_model=JobSearchListResponse)
def search_jobs_alias(
    conn: DbConnection,
    q: str | None = Query(default=None, max_length=200),
    keyword: str | None = Query(default=None, max_length=200),
    title: str | None = None,
    company_name: str | None = None,
    company_industry: str | None = None,
    industry: str | None = None,
    category: str | None = None,
    department: str | None = None,
    location_city: str | None = Query(default=None, alias="location.city"),
    location: str | None = None,
    location_country: str | None = Query(default=None, alias="location.country"),
    remote: bool | None = None,
    remote_type: str | None = None,
    workingModel: str | None = None,
    employmentType: str | None = None,
    employment_type: str | None = None,
    experienceLevel: str | None = None,
    skills: str | None = None,
    categories: str | None = None,
    tags: str | None = None,
    salaryMin: float | None = Query(default=None, ge=0),
    salaryMax: float | None = Query(default=None, ge=0),
    salary_min: float | None = Query(default=None, ge=0),
    salary_max: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort: str | None = "newest",
) -> JobSearchListResponse:
    return search_jobs_response(
        conn,
        keyword=keyword,
        q=q,
        title=title,
        company_name=company_name,
        company_industry=company_industry,
        industry=industry,
        category=category,
        department=department,
        location_city=location_city,
        location=location,
        location_country=location_country,
        remote=remote,
        remote_type=remote_type,
        working_model=workingModel,
        employment_type=employmentType or employment_type,
        seniority=experienceLevel,
        skills=skills,
        categories=categories,
        tags=tags,
        salary_min=salaryMin if salaryMin is not None else salary_min,
        salary_max=salaryMax if salaryMax is not None else salary_max,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/cvs", response_model=CVSearchListResponse)
def search_cvs_alias(
    conn: DbConnection,
    q: str | None = Query(default=None, max_length=200),
    keyword: str | None = Query(default=None, max_length=200),
    fullname: str | None = None,
    headline: str | None = None,
    target_role: str | None = None,
    targetRole: str | None = None,
    location_city: str | None = Query(default=None, alias="location.city"),
    location: str | None = None,
    location_country: str | None = Query(default=None, alias="location.country"),
    desiredIndustry: str | None = None,
    experienceLevel: str | None = None,
    educationLevel: str | None = None,
    workingModel: str | None = None,
    employmentType: str | None = None,
    employment_type: str | None = None,
    availability: str | None = None,
    skills: str | None = None,
    tags: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort: str | None = "newest",
) -> CVSearchListResponse:
    return search_cvs_response(
        conn,
        q=q,
        keyword=keyword,
        fullname=fullname,
        headline=headline,
        target_role=target_role,
        targetRole=targetRole,
        location_city=location_city,
        location=location,
        location_country=location_country,
        desiredIndustry=desiredIndustry,
        experienceLevel=experienceLevel,
        educationLevel=educationLevel,
        workingModel=workingModel,
        employmentType=employmentType,
        employment_type=employment_type,
        availability=availability,
        skills=skills,
        tags=tags,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/candidates", response_model=CVSearchListResponse)
def search_candidates_alias(
    conn: DbConnection,
    q: str | None = Query(default=None, max_length=200),
    keyword: str | None = Query(default=None, max_length=200),
    fullname: str | None = None,
    headline: str | None = None,
    target_role: str | None = None,
    targetRole: str | None = None,
    location_city: str | None = Query(default=None, alias="location.city"),
    location: str | None = None,
    location_country: str | None = Query(default=None, alias="location.country"),
    desiredIndustry: str | None = None,
    experienceLevel: str | None = None,
    educationLevel: str | None = None,
    workingModel: str | None = None,
    employmentType: str | None = None,
    employment_type: str | None = None,
    availability: str | None = None,
    skills: str | None = None,
    tags: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort: str | None = "newest",
) -> CVSearchListResponse:
    return search_cvs_alias(
        conn=conn,
        q=q,
        keyword=keyword,
        fullname=fullname,
        headline=headline,
        target_role=target_role,
        targetRole=targetRole,
        location_city=location_city,
        location=location,
        location_country=location_country,
        desiredIndustry=desiredIndustry,
        experienceLevel=experienceLevel,
        educationLevel=educationLevel,
        workingModel=workingModel,
        employmentType=employmentType,
        employment_type=employment_type,
        availability=availability,
        skills=skills,
        tags=tags,
        page=page,
        limit=limit,
        sort=sort,
    )
