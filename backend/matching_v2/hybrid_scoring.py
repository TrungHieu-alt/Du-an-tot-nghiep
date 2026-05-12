"""Hybrid scoring rules for the additive matching-hybrid endpoints."""

from __future__ import annotations

from dataclasses import fields
from typing import Optional

from .hybrid_models import (
    FailedFilter,
    HybridBreakdown,
    HybridPairResult,
    SkippedGroup,
    WeightedGroupScore,
)
from .hybrid_utils import (
    clamp_score,
    has_value,
    is_empty_value,
    normalize_text,
    normalize_weights,
    safe_join,
    should_skip_group,
    text_similarity,
)
from .models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
)
from .scoring import cosine_similarity
from .skill_normalizer import normalize_skills, skill_coverage


GROUP_WEIGHTS: dict[str, float] = {
    "title_score": 0.08,
    "skills_score": 0.32,
    "experience_score": 0.22,
    "project_score": 0.10,
    "seniority_score": 0.08,
    "education_score": 0.05,
    "certification_score": 0.05,
    "language_score": 0.04,
    "location_score": 0.03,
    "salary_score": 0.02,
    "job_type_score": 0.01,
}

SENIORITY_RANK: dict[str, int] = {
    "intern": 0,
    "fresher": 1,
    "junior": 2,
    "mid": 3,
    "middle": 3,
    "senior": 4,
    "lead": 5,
}

EDUCATION_RANK: dict[str, int] = {
    "lop_9": 0,
    "high_school": 0,
    "lop_12": 1,
    "college": 1,
    "dai_hoc": 2,
    "bachelor": 2,
    "thac_si": 3,
    "master": 3,
    "tien_si": 4,
    "phd": 4,
}

MISSING_SCHEMA_GROUPS = {
    "project_score": "Current V2 schema has no project fields.",
    "language_score": "Current V2 schema has no language fields.",
    "salary_score": "Current V2 schema has no salary fields.",
}


def _semantic_or_text_score(
    left_embedding: Optional[list[float]],
    right_embedding: Optional[list[float]],
    left_text: str,
    right_text: str,
) -> tuple[float, bool]:
    if left_embedding is not None and right_embedding is not None:
        return cosine_similarity(left_embedding, right_embedding) * 100.0, False
    return text_similarity(left_text, right_text), True


def _add_score(
    valid_scores: list[WeightedGroupScore],
    breakdown: HybridBreakdown,
    group: str,
    score: float,
) -> None:
    rounded = round(clamp_score(score), 6)
    setattr(breakdown, group, rounded)
    valid_scores.append(
        WeightedGroupScore(group=group, score=rounded, weight=GROUP_WEIGHTS[group])
    )


def _skip(skipped: list[SkippedGroup], group: str, reason: str) -> None:
    skipped.append(SkippedGroup(group=group, reason=reason))


def _fail(failed: list[FailedFilter], field: str, reason: str) -> None:
    failed.append(FailedFilter(field=field, reason=reason))


def _score_title(
    job: JobPostV2,
    job_emb: Optional[JobEmbeddingsV2],
    cv: CandidateProfileV2,
    cv_emb: Optional[CandidateEmbeddingsV2],
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    warnings: list[str],
    explanations: dict[str, str],
) -> None:
    job_text = safe_join([job.title, job.seniority])
    cv_text = safe_join([cv.title, cv.seniority])
    if should_skip_group(job_text, cv_text):
        _skip(skipped, "title_score", "Job title/seniority is empty, so title scoring was skipped.")
        return
    if is_empty_value(cv_text):
        _add_score(valid_scores, breakdown, "title_score", 0.0)
        explanations["title"] = "Job has title/seniority data but CV title/seniority is empty."
        return
    score, used_text_fallback = _semantic_or_text_score(
        job_emb.emb_title if job_emb else None,
        cv_emb.emb_title if cv_emb else None,
        job_text,
        cv_text,
    )
    if used_text_fallback:
        warnings.append(
            "MiniLM title embeddings are unavailable; used deterministic text similarity."
        )
    _add_score(valid_scores, breakdown, "title_score", score)
    explanations["title"] = "Title score compares JD title/seniority with CV title/seniority."


def _score_skills(
    job: JobPostV2,
    job_emb: Optional[JobEmbeddingsV2],
    cv: CandidateProfileV2,
    cv_emb: Optional[CandidateEmbeddingsV2],
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    warnings: list[str],
    explanations: dict[str, str],
) -> None:
    if should_skip_group(job.skills, cv.skills):
        _skip(skipped, "skills_score", "Job skills are empty, so skills scoring was skipped.")
        return
    if is_empty_value(cv.skills):
        _add_score(valid_scores, breakdown, "skills_score", 0.0)
        explanations["skills"] = "Job has skills but CV skills are empty."
        return

    coverage, matched = skill_coverage(job.skills, cv.skills)
    semantic, used_text_fallback = _semantic_or_text_score(
        job_emb.emb_skills if job_emb else None,
        cv_emb.emb_skills if cv_emb else None,
        ", ".join(normalize_skills(job.skills)),
        ", ".join(normalize_skills(cv.skills)),
    )
    if used_text_fallback:
        warnings.append(
            "MiniLM skill embeddings are unavailable; used deterministic text similarity."
        )
    score = (coverage * 100.0 * 0.50) + (semantic * 0.50)
    _add_score(valid_scores, breakdown, "skills_score", score)
    explanations["skills"] = (
        f"Candidate matches {len(matched)}/{len(normalize_skills(job.skills))} "
        "legacy JD skills exactly or by alias."
    )


def _score_experience(
    job: JobPostV2,
    job_emb: Optional[JobEmbeddingsV2],
    cv: CandidateProfileV2,
    cv_emb: Optional[CandidateEmbeddingsV2],
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    warnings: list[str],
    explanations: dict[str, str],
) -> None:
    job_text = normalize_text(job.requirement)
    cv_exp_text = normalize_text(cv.experience)
    cv_summary_text = normalize_text(cv.summary)
    cv_text = safe_join([cv.experience, cv.summary])
    if should_skip_group(job_text, cv_text):
        _skip(skipped, "experience_score", "Job requirement is empty, so experience scoring was skipped.")
        return
    if is_empty_value(cv_text):
        _add_score(valid_scores, breakdown, "experience_score", 0.0)
        explanations["experience"] = "Job has requirements but CV experience/summary is empty."
        return

    req_exp, used_exp_fallback = _semantic_or_text_score(
        job_emb.emb_requirement if job_emb else None,
        cv_emb.emb_experience if cv_emb else None,
        job_text,
        cv_exp_text,
    )
    req_summary, used_summary_fallback = _semantic_or_text_score(
        job_emb.emb_requirement if job_emb else None,
        cv_emb.emb_summary if cv_emb else None,
        job_text,
        cv_summary_text,
    )
    if used_exp_fallback or used_summary_fallback:
        warnings.append(
            "MiniLM experience embeddings are unavailable; used deterministic text similarity."
        )
    score = (req_exp * 0.70) + (req_summary * 0.30)
    _add_score(valid_scores, breakdown, "experience_score", score)
    explanations["experience"] = "Experience score blends JD requirement vs CV experience and summary."


def _score_seniority(
    job: JobPostV2,
    cv: CandidateProfileV2,
    strict_filters: bool,
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    failed: list[FailedFilter],
    warnings: list[str],
    explanations: dict[str, str],
) -> None:
    job_value = normalize_text(job.seniority)
    cv_value = normalize_text(cv.seniority)
    if should_skip_group(job_value, cv_value):
        _skip(skipped, "seniority_score", "Job seniority is empty, so seniority scoring was skipped.")
        return
    if is_empty_value(cv_value) or cv_value not in SENIORITY_RANK:
        _add_score(valid_scores, breakdown, "seniority_score", 0.0)
        if strict_filters:
            _fail(failed, "seniority", "CV seniority is missing or unknown.")
        return

    job_rank = SENIORITY_RANK.get(job_value)
    if job_rank is None:
        _skip(skipped, "seniority_score", "Job seniority is unknown, so seniority scoring was skipped.")
        return

    diff = SENIORITY_RANK[cv_value] - job_rank
    if diff == 0:
        score = 100.0
    elif diff == -1:
        score = 70.0
    elif diff < -1:
        score = 20.0
        if strict_filters:
            _fail(failed, "seniority", "CV seniority is much lower than JD seniority.")
    elif diff == 1:
        score = 95.0
    elif diff == 2:
        score = 90.0
        warnings.append("Candidate may be overqualified.")
    else:
        score = 85.0
        warnings.append("Candidate may be overqualified.")

    _add_score(valid_scores, breakdown, "seniority_score", score)
    explanations["seniority"] = f"JD seniority={job_value}; CV seniority={cv_value}."


def _score_education(
    job: JobPostV2,
    cv: CandidateProfileV2,
    strict_filters: bool,
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    failed: list[FailedFilter],
    explanations: dict[str, str],
) -> None:
    job_value = normalize_text(job.education)
    cv_value = normalize_text(cv.education)
    if should_skip_group(job_value, cv_value):
        _skip(skipped, "education_score", "Job education is empty, so education scoring was skipped.")
        return
    job_rank = EDUCATION_RANK.get(job_value)
    cv_rank = EDUCATION_RANK.get(cv_value)
    if job_rank is None:
        _skip(skipped, "education_score", "Job education is unknown, so education scoring was skipped.")
        return
    if cv_rank is None:
        _add_score(valid_scores, breakdown, "education_score", 0.0)
        if strict_filters:
            _fail(failed, "education", "CV education is missing or unknown.")
        return
    if cv_rank >= job_rank:
        score = 100.0
    else:
        score = 0.0
        if strict_filters:
            _fail(failed, "education", "CV education is lower than JD education requirement.")
    _add_score(valid_scores, breakdown, "education_score", score)
    explanations["education"] = f"JD education={job_value}; CV education={cv_value}."


def _score_certifications(
    job: JobPostV2,
    cv: CandidateProfileV2,
    strict_filters: bool,
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    failed: list[FailedFilter],
    explanations: dict[str, str],
) -> None:
    required = normalize_skills(job.required_certifications)
    candidate = set(normalize_skills(cv.certifications))
    if not required:
        reason = (
            "Both JD and CV certifications are empty and no certification is required."
            if not candidate
            else "JD has no certification requirement, so CV certifications were not scored."
        )
        _skip(
            skipped,
            "certification_score",
            reason,
        )
        return
    if not candidate:
        _add_score(valid_scores, breakdown, "certification_score", 0.0)
        if strict_filters:
            _fail(failed, "certification", "JD requires certifications but CV certifications are empty.")
        explanations["certification"] = "Candidate has no certifications for required JD certifications."
        return
    matched = sorted(set(required) & candidate)
    score = (len(matched) / len(required)) * 100.0
    if len(matched) < len(required) and strict_filters:
        missing = sorted(set(required) - candidate)
        _fail(failed, "certification", f"Missing required certifications: {', '.join(missing)}.")
    _add_score(valid_scores, breakdown, "certification_score", score)
    explanations["certification"] = f"Candidate matches {len(matched)}/{len(required)} required certifications."


def _score_location(
    job: JobPostV2,
    cv: CandidateProfileV2,
    strict_filters: bool,
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    failed: list[FailedFilter],
    explanations: dict[str, str],
) -> None:
    job_type = normalize_text(job.job_type)
    if job_type == "remote":
        _add_score(valid_scores, breakdown, "location_score", 100.0)
        explanations["location"] = "Job is remote, so location does not need to match."
        return

    job_location = normalize_text(job.location)
    cv_location = normalize_text(cv.location)
    if should_skip_group(job_location, cv_location):
        _skip(skipped, "location_score", "Job location is empty, so location scoring was skipped.")
        return
    if is_empty_value(cv_location):
        _add_score(valid_scores, breakdown, "location_score", 0.0)
        if strict_filters:
            _fail(failed, "location", "CV location is missing.")
        return
    if job_location == cv_location:
        score = 100.0
        explanations["location"] = "JD and CV location match exactly."
    else:
        score = 0.0
        explanations["location"] = "JD and CV location do not match."
        if strict_filters:
            _fail(failed, "location", "JD and CV location do not match for a non-remote job.")
    _add_score(valid_scores, breakdown, "location_score", score)


def _score_job_type(
    job: JobPostV2,
    cv: CandidateProfileV2,
    strict_filters: bool,
    breakdown: HybridBreakdown,
    valid_scores: list[WeightedGroupScore],
    skipped: list[SkippedGroup],
    failed: list[FailedFilter],
    explanations: dict[str, str],
) -> None:
    job_type = normalize_text(job.job_type)
    cv_type = normalize_text(cv.job_type)
    if should_skip_group(job_type, cv_type):
        _skip(skipped, "job_type_score", "Job type is empty, so job type scoring was skipped.")
        return
    if is_empty_value(cv_type):
        _add_score(valid_scores, breakdown, "job_type_score", 0.0)
        if strict_filters:
            _fail(failed, "job_type", "CV job type is missing.")
        return
    score = 100.0 if job_type == cv_type else 0.0
    if score == 0.0 and strict_filters:
        _fail(failed, "job_type", "JD and CV job_type values do not match.")
    _add_score(valid_scores, breakdown, "job_type_score", score)
    explanations["job_type"] = f"JD job_type={job_type}; CV job_type={cv_type}."


def evaluate_pair_hybrid(
    job: JobPostV2,
    job_emb: Optional[JobEmbeddingsV2],
    cv: CandidateProfileV2,
    cv_emb: Optional[CandidateEmbeddingsV2],
    strict_filters: bool = True,
) -> HybridPairResult:
    breakdown = HybridBreakdown()
    skipped: list[SkippedGroup] = []
    failed: list[FailedFilter] = []
    warnings: list[str] = []
    explanations: dict[str, str] = {}
    valid_scores: list[WeightedGroupScore] = []

    _score_title(job, job_emb, cv, cv_emb, breakdown, valid_scores, skipped, warnings, explanations)
    _score_skills(job, job_emb, cv, cv_emb, breakdown, valid_scores, skipped, warnings, explanations)
    _score_experience(job, job_emb, cv, cv_emb, breakdown, valid_scores, skipped, warnings, explanations)
    _score_seniority(
        job, cv, strict_filters, breakdown, valid_scores, skipped, failed, warnings, explanations
    )
    _score_education(job, cv, strict_filters, breakdown, valid_scores, skipped, failed, explanations)
    _score_certifications(job, cv, strict_filters, breakdown, valid_scores, skipped, failed, explanations)
    _score_location(job, cv, strict_filters, breakdown, valid_scores, skipped, failed, explanations)
    _score_job_type(job, cv, strict_filters, breakdown, valid_scores, skipped, failed, explanations)

    for group, reason in MISSING_SCHEMA_GROUPS.items():
        _skip(skipped, group, reason)

    weights = normalize_weights({score.group: score.weight for score in valid_scores})
    if not weights:
        final_score = 0.0
        passed = False
        warnings.append("Not enough comparable data to calculate match score.")
    else:
        scores_by_group = {score.group: score.score for score in valid_scores}
        final_score = sum(scores_by_group[group] * weight for group, weight in weights.items())
        passed = len(failed) == 0

    # Keep explicit None for groups that were not calculated.
    valid_group_names = {score.group for score in valid_scores}
    for field in fields(HybridBreakdown):
        if field.name not in valid_group_names and getattr(breakdown, field.name) is not None:
            setattr(breakdown, field.name, None)

    return HybridPairResult(
        job_id=job.job_id,
        cv_id=cv.cv_id,
        final_score=round(clamp_score(final_score), 6),
        passed=passed,
        breakdown=breakdown,
        skipped_groups=skipped,
        failed_filters=failed,
        warnings=warnings,
        explanations=explanations,
    )
