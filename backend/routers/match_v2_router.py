from dataclasses import asdict

from fastapi import APIRouter, Body, HTTPException

from matching_v2 import get_connection, run_for_cv, run_for_job
from schemas.match_v2_schema import (
    ErrorDetailResponse,
    RunMatchingV2Request,
    RunMatchingV2Response,
)

router = APIRouter(prefix="/v2/prototype/matching", tags=["matching-v2-prototype"])


@router.post(
    "/job/{job_id}/run",
    response_model=RunMatchingV2Response,
    responses={404: {"model": ErrorDetailResponse}},
)
def run_matching_v2_for_job(
    job_id: int,
    request: RunMatchingV2Request = Body(default_factory=RunMatchingV2Request),
):
    try:
        conn = get_connection()
        try:
            result = run_for_job(
                conn=conn,
                job_id=job_id,
                top_k=request.top_k,
                min_score=request.min_score,
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
    response_model=RunMatchingV2Response,
    responses={404: {"model": ErrorDetailResponse}},
)
def run_matching_v2_for_cv(
    cv_id: int,
    request: RunMatchingV2Request = Body(default_factory=RunMatchingV2Request),
):
    try:
        conn = get_connection()
        try:
            result = run_for_cv(
                conn=conn,
                cv_id=cv_id,
                top_k=request.top_k,
                min_score=request.min_score,
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
