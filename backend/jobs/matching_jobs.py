import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.match_service import MatchingService


class MatchingJobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        async with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "result": None,
                "error": None,
            }
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def mark_running(self, job_id: str) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "running"
                self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    async def mark_succeeded(self, job_id: str, result: Dict[str, Any]) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "succeeded"
                self._jobs[job_id]["result"] = result
                self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    async def mark_failed(self, job_id: str, error: str) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["error"] = error
                self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()


matching_job_store = MatchingJobStore()


async def run_job_to_cv(job_tracking_id: str, job_id: int, top_k: int, min_score: float) -> None:
    await matching_job_store.mark_running(job_tracking_id)
    try:
        result = await MatchingService.run_matching_for_job(
            job_id=job_id,
            top_k=top_k,
            min_score=min_score,
        )
        await matching_job_store.mark_succeeded(job_tracking_id, result)
    except Exception as exc:
        await matching_job_store.mark_failed(job_tracking_id, str(exc))


async def run_cv_to_job(job_tracking_id: str, cv_id: int, top_k: int, min_score: float) -> None:
    await matching_job_store.mark_running(job_tracking_id)
    try:
        result = await MatchingService.run_matching_for_cv(
            cv_id=cv_id,
            top_k=top_k,
            min_score=min_score,
        )
        await matching_job_store.mark_succeeded(job_tracking_id, result)
    except Exception as exc:
        await matching_job_store.mark_failed(job_tracking_id, str(exc))
