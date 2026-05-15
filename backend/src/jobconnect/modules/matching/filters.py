"""Hard-filter pure functions for production matching.

All functions are stateless and accept explicit arguments so they are trivially
unit-testable without a database connection.

Rules: docs/REQUIREMENTS.md and production matching HLD.
"""

from __future__ import annotations

from .models import CandidateProfileMatch, JobPostMatch

# Education hierarchy: lower index = lower level.
# Pass condition: CV education rank >= JD education rank.
EDUCATION_RANK: dict[str, int] = {
    "lop_9": 0,
    "lop_12": 1,
    "dai_hoc": 2,
    "thac_si": 3,
    "tien_si": 4,
}


# ---------------------------------------------------------------------------
# Individual filter predicates (each returns True = pass)
# ---------------------------------------------------------------------------

def passes_job_type(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
    """job_type must match exactly on both sides."""
    return job.job_type == cv.job_type


def passes_location(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
    """If JD is remote, location is ignored. Otherwise exact match required."""
    if job.job_type == "remote":
        return True
    return job.location == cv.location


def passes_seniority(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
    """Seniority must match exactly."""
    return job.seniority == cv.seniority


def passes_education(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
    """CV education must be >= JD required education in the taxonomy.

    If either value is absent from the taxonomy (should not happen given DB
    constraints) the pair fails the filter per REQUIREMENTS.md §9.
    """
    jd_rank = EDUCATION_RANK.get(job.education)
    cv_rank = EDUCATION_RANK.get(cv.education)
    if jd_rank is None or cv_rank is None:
        return False
    return cv_rank >= jd_rank


def passes_certifications(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
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

def passes_hard_filter(job: JobPostMatch, cv: CandidateProfileMatch) -> bool:
    """Return True iff the CV passes all hard filters for the given job."""
    return (
        passes_job_type(job, cv)
        and passes_location(job, cv)
        and passes_seniority(job, cv)
        and passes_education(job, cv)
        and passes_certifications(job, cv)
    )
