from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from matching_v2 import get_connection, run_for_cv, run_for_job
from schemas.match_v2_schema import RunMatchingV2Request, RunMatchingV2Response

router = APIRouter(prefix="/v2/prototype/matching", tags=["matching-v2-prototype"])


def _validate_run_request(top_k: int, min_score: float) -> None:
    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be in range [1, 10]")
    if min_score < 0.0 or min_score > 1.0:
        raise ValueError("min_score must be in range [0.0, 1.0]")


@router.post("/job/{job_id}/run", response_model=RunMatchingV2Response)
def run_matching_v2_for_job(job_id: int, request: RunMatchingV2Request):
    try:
        _validate_run_request(request.top_k, request.min_score)
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
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/cv/{cv_id}/run", response_model=RunMatchingV2Response)
def run_matching_v2_for_cv(cv_id: int, request: RunMatchingV2Request):
    try:
        _validate_run_request(request.top_k, request.min_score)
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
            raise HTTPException(status_code=404, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
