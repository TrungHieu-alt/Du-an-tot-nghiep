from dataclasses import asdict

from fastapi import APIRouter, Body, HTTPException

from matching_v2.db import get_connection
from matching_v2.hybrid_runner import run_hybrid_for_cv, run_hybrid_for_job
from schemas.match_hybrid_schema import (
    ErrorDetailResponse,
    RunMatchingHybridRequest,
    RunMatchingHybridResponse,
)


router = APIRouter(
    prefix="/v2/prototype/matching-hybrid",
    tags=["matching-v2-hybrid-prototype"],
)


@router.post(
    "/job/{job_id}/run",
    response_model=RunMatchingHybridResponse,
    responses={404: {"model": ErrorDetailResponse}},
    summary="Run hybrid matching for a job anchor",
    description=(
        "Additive hybrid matcher over the current V2 PostgreSQL schema. "
        "Scores are returned on a 0..100 scale with breakdown, skipped groups, "
        "failed filters, warnings, and explanations. Existing V2 matching "
        "endpoints are unchanged."
    ),
)
def run_matching_hybrid_for_job(
    job_id: int,
    request: RunMatchingHybridRequest = Body(default_factory=RunMatchingHybridRequest),
):
    try:
        conn = get_connection()
        try:
            result = run_hybrid_for_job(
                conn=conn,
                job_id=job_id,
                top_k=request.top_k,
                min_score=request.min_score,
                include_failed=request.include_failed,
                strict_filters=request.strict_filters,
            )
            return asdict(result)
        finally:
            conn.close()
    except ValueError as exc:
        message = str(exc)
        if "not found" in message:
            raise HTTPException(status_code=404, detail="job not found") from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/cv/{cv_id}/run",
    response_model=RunMatchingHybridResponse,
    responses={404: {"model": ErrorDetailResponse}},
    summary="Run hybrid matching for a CV anchor",
    description=(
        "Mirror of the hybrid job endpoint: anchor a `cv_id` and rank job "
        "posts using the additive hybrid scorer."
    ),
)
def run_matching_hybrid_for_cv(
    cv_id: int,
    request: RunMatchingHybridRequest = Body(default_factory=RunMatchingHybridRequest),
):
    try:
        conn = get_connection()
        try:
            result = run_hybrid_for_cv(
                conn=conn,
                cv_id=cv_id,
                top_k=request.top_k,
                min_score=request.min_score,
                include_failed=request.include_failed,
                strict_filters=request.strict_filters,
            )
            return asdict(result)
        finally:
            conn.close()
    except ValueError as exc:
        message = str(exc)
        if "not found" in message:
            raise HTTPException(status_code=404, detail="cv not found") from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
