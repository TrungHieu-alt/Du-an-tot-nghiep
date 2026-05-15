from __future__ import annotations

from fastapi import APIRouter

from jobconnect.modules.api.router import ALL_API_ROUTERS
from jobconnect.modules.system import router as system_router


API_DESCRIPTION = """\
Backend API for the JobConnect MVP recruiting marketplace.

The active surface is the `/api/*` namespace for auth, profiles, documents,
jobs, resumes, matching, applications, invites, notifications, and admin
monitoring. Legacy `/api/v2/prototype/*` runtime code has been removed.
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Registration, login, logout, and JWT issuance."},
    {"name": "me", "description": "Current user identity."},
    {"name": "candidate", "description": "Candidate profile, resumes, and resume search."},
    {"name": "recruiter", "description": "Recruiter profile management."},
    {"name": "organizations", "description": "Employer organization profile data."},
    {"name": "jobs", "description": "Job post CRUD, publishing, and job search."},
    {"name": "documents", "description": "Uploaded document metadata and parse jobs."},
    {"name": "matching", "description": "Two-way explainable JD/CV matching."},
    {"name": "applications", "description": "Candidate applications and status transitions."},
    {"name": "invites", "description": "Recruiter invite lifecycle."},
    {"name": "notifications", "description": "In-app notifications."},
    {"name": "admin", "description": "Read-only admin monitoring."},
    {"name": "system", "description": "Health checks and runtime probes."},
    {"name": "root", "description": "Service root."},
]

API_PREFIX = "/api"
APP_ROUTERS: tuple[APIRouter, ...] = (*ALL_API_ROUTERS, system_router.router)
