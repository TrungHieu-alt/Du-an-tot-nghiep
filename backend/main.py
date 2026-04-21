from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware   # ← thêm dòng này
from db import init_db
from routers import (
    user_router,
    candidate_router,
    recruiter_router,
    job_router,
    cv_router,
    application_router,
    match_router,
    system_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("✓ Database initialized")
    yield
    # Shutdown
    print("✓ Shutdown complete")


app = FastAPI(
    title="Job Matcher API",
    description="Backend API for Mastodon Job Matcher Extension",
    version="1.0.0",
    lifespan=lifespan,
)

# ------------------------------
# 🔥 Enable CORS here
# ------------------------------
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
# ------------------------------


# Include routers
app.include_router(user_router.router, prefix="/api")
app.include_router(candidate_router.router, prefix="/api")
app.include_router(recruiter_router.router, prefix="/api")
app.include_router(job_router.router, prefix="/api")
app.include_router(cv_router.router, prefix="/api")
app.include_router(application_router.router, prefix="/api")
app.include_router(match_router.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")



@app.get("/")
async def root():
    return {"message": "Welcome to Job Matcher API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
