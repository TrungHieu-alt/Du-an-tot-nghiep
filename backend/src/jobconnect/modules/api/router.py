from __future__ import annotations

from jobconnect.modules.admin.router import router as admin_router
from jobconnect.modules.api import shared
from jobconnect.modules.applications.router import router as applications_router
from jobconnect.modules.auth.router import router as auth_router
from jobconnect.modules.documents.router import router as documents_router
from jobconnect.modules.documents.service import MAX_DOCUMENT_BYTES
from jobconnect.modules.invites.router import router as invites_router
from jobconnect.modules.jobs.router import router as jobs_router
from jobconnect.modules.matching.router import router as matching_router
from jobconnect.modules.notifications.router import router as notifications_router
from jobconnect.modules.organizations.router import router as organizations_router
from jobconnect.modules.resumes.router import router as candidate_resumes_router
from jobconnect.modules.users.router import (
    candidate_router,
    me_router,
    recruiter_router,
)

# Compatibility re-exports used by app wiring and tests.
get_connection = shared.get_connection
get_storage = shared.get_storage
get_parser = shared.get_parser
get_embedding_provider = shared.get_embedding_provider
hash_password = shared.hash_password
verify_password = shared.verify_password
_jwt_secret = shared._jwt_secret
_jwt_ttl_seconds = shared._jwt_ttl_seconds
create_access_token = shared.create_access_token
parse_token = shared.parse_token
CurrentUser = shared.CurrentUser
current_user = shared.current_user
require_active = shared.require_active
require_roles = shared.require_roles
business_error = shared.business_error
to_error_envelope = shared.to_error_envelope
APIModel = shared.APIModel
Paginated = shared.Paginated

ALL_API_ROUTERS = [
    auth_router,
    me_router,
    candidate_router,
    recruiter_router,
    organizations_router,
    candidate_resumes_router,
    jobs_router,
    documents_router,
    matching_router,
    applications_router,
    invites_router,
    notifications_router,
    admin_router,
]
