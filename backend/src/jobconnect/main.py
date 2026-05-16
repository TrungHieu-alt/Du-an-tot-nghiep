from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from jobconnect.app import API_DESCRIPTION, API_PREFIX, APP_ROUTERS, OPENAPI_TAGS
from jobconnect.modules.api.router import to_error_envelope
from jobconnect.modules.api.shared import ErrorBody, ErrorEnvelope


app = FastAPI(
    title="Job Matcher API",
    description=API_DESCRIPTION,
    version="3.0.0",
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "JobConnect Engineering"},
)

def _cors_origins() -> list[str]:
    """Return allowed CORS origins from CORS_ORIGINS env var (comma-separated).

    Defaults cover local Vite (5173) and Next.js (3000) dev servers.
    Override in production: CORS_ORIGINS=https://app.example.com
    """
    import os
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in APP_ROUTERS:
    app.include_router(router, prefix=API_PREFIX)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=to_error_envelope(exc.detail, exc.status_code),
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    fields = {
        ".".join(str(part) for part in err["loc"]): err["msg"]
        for err in exc.errors()
    }
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "fields": fields,
            }
        },
    )


@app.get(
    "/",
    tags=["root"],
    summary="Service root",
    description=(
        "Service banner endpoint. Returns a welcome payload; use "
        "`GET /api/health` for the liveness probe used by Docker Compose."
    ),
)
async def root():
    return {"message": "Job Matcher API Production MVP"}


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    schemas = schema.setdefault("components", {}).setdefault("schemas", {})
    for model in (ErrorBody, ErrorEnvelope):
        raw = model.model_json_schema(mode="serialization", ref_template="#/components/schemas/{model}")
        defs = raw.pop("$defs", {})
        schemas[model.__name__] = raw
        schemas.update(defs)
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
