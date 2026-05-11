from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    summary="Liveness probe",
    description=(
        "Lightweight liveness check used by the docker-compose healthcheck "
        "and by clients to verify connectivity. Returns `{\"status\":\"ok\"}` "
        "as long as the FastAPI process can serve requests. Does NOT verify "
        "downstream dependencies (Mongo, Postgres)."
    ),
)
async def health_check():
    return {"status": "ok"}