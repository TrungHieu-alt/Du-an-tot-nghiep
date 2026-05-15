"""Hard-filter pure functions for Matching V2.

All functions are stateless and accept explicit arguments so they are trivially
unit-testable without a database connection.

Rules: docs/REQUIREMENTS.md §3 (FR2 Stage 2) and §9 (Default Decisions).
"""

from __future__ import annotations

from .models import CandidateProfileV2, JobPostV2

# Education hierarchy: lower index = lower level.
# Pass condition: CV education rank >= JD education rank.
EDUCATION_RANK: dict[str, int] = {
    "unknown": 0,
    "high_school": 1,
    "bachelor": 2,
    "master": 3,
    "phd": 4,
}


# ---------------------------------------------------------------------------
# Individual filter predicates (each returns True = pass)
# ---------------------------------------------------------------------------

def passes_job_type(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """job_type must match exactly on both sides."""
    return job.job_type == cv.job_type


def passes_location(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """If JD is remote, location is ignored. Otherwise exact match required."""
    if job.job_type == "remote":
        return True
    return job.location == cv.location


def passes_seniority(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """Seniority must match exactly (no alias inference in prototype)."""
    return job.seniority == cv.seniority


def passes_education(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """CV education must be >= JD required education in the taxonomy.

    If either value is absent from the taxonomy (should not happen given DB
    constraints) the pair fails the filter per REQUIREMENTS.md §9.
    """
    jd_rank = EDUCATION_RANK.get(job.education)
    cv_rank = EDUCATION_RANK.get(cv.education)
    if jd_rank is None or cv_rank is None:
        return False
    return cv_rank >= jd_rank


def passes_certifications(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """All JD required_certifications must be present in CV certifications.

    Empty required_certifications always passes.
    """
    required = set(job.required_certifications)
    if not required:
        return True
    return required.issubset(set(cv.certifications))


# ---------------------------------------------------------------------------
# Composite hard filter
# ---------------------------------------------------------------------------

def passes_hard_filter(job: JobPostV2, cv: CandidateProfileV2) -> bool:
    """Return True iff the CV passes all hard filters for the given job."""
    return (
        passes_job_type(job, cv)
        and passes_location(job, cv)
        and passes_seniority(job, cv)
        and passes_education(job, cv)
        and passes_certifications(job, cv)
    )
