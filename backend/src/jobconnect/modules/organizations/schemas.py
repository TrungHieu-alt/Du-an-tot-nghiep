from __future__ import annotations

from typing import Optional

from pydantic import Field

from jobconnect.modules.api.shared import APIModel


class OrganizationRequest(APIModel):
    name: str = Field(min_length=1)
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    about: Optional[str] = None


class Organization(OrganizationRequest):
    organization_id: int
