from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from jobconnect.modules.api.shared import CurrentUser, Paginated, current_user, require_roles
from jobconnect.modules.organizations import service
from jobconnect.modules.organizations.schemas import Organization, OrganizationRequest

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=Paginated)
def list_organizations(
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(current_user),
):
    return service.list_organizations(q, limit, offset)


@router.post("", response_model=Organization, status_code=201)
def create_organization(
    request: OrganizationRequest,
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.create_organization(request, user)


@router.get("/{organization_id}", response_model=Organization)
def get_organization(organization_id: int, _: CurrentUser = Depends(current_user)):
    return service.get_organization(organization_id)


@router.patch("/{organization_id}", response_model=Organization)
def update_organization(
    organization_id: int,
    request: OrganizationRequest,
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    return service.update_organization(organization_id, request, user)
