"""Compatibility imports for normal search schemas.

Normal Job/CV storage now lives in dedicated schema modules. This file keeps
existing imports stable for tests and callers that still import the old normal
search schema module.
"""

from schemas.normal_cv_schema import CVSearchListItem, CVSearchListResponse
from schemas.normal_job_schema import (
    JobSearchFiltersResponse,
    JobSearchListItem,
    JobSearchListResponse,
)

__all__ = [
    "CVSearchListItem",
    "CVSearchListResponse",
    "JobSearchFiltersResponse",
    "JobSearchListItem",
    "JobSearchListResponse",
]
