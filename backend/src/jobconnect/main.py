from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from jobconnect.app import API_DESCRIPTION, API_PREFIX, APP_ROUTERS, OPENAPI_TAGS
from jobconnect.modules.api.router import to_error_envelope


app = FastAPI(
    title="Job Matcher API",
    description=API_DESCRIPTION,
    version="3.0.0",
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "JobConnect Engineering"},
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
