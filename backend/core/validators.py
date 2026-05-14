"""Validation wrappers for normalized non-V2 CV/Job payloads."""

from __future__ import annotations

from typing import Any

from core.normalizers import normalize_cv_payload, normalize_job_payload


def validate_cv_payload(data: dict[str, Any], *, for_create: bool = False, include_missing: bool = False) -> dict[str, Any]:
    return normalize_cv_payload(data, for_create=for_create, include_missing=include_missing)


def validate_job_payload(data: dict[str, Any], *, for_create: bool = False, include_missing: bool = False) -> dict[str, Any]:
    return normalize_job_payload(data, for_create=for_create, include_missing=include_missing)

