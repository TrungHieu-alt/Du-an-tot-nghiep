"""Matching V2 run-only orchestrator.

Entry points:
    run_for_job(conn, job_id, top_k, min_score) -> RunMatchingV2Response
    run_for_cv(conn, cv_id, top_k, min_score)   -> RunMatchingV2Response

No writes. No persistence. No LLM.
Source: docs/REQUIREMENTS.md §3 (FR2 Stage 1-4), §5.5, §9.
"""

from __future__ import annotations

import time
from typing import Optional

import psycopg

from .db import (
    load_all_candidate_embeddings,
    load_all_candidates,
    load_all_job_embeddings,
    load_all_jobs,
    load_candidate,
    load_candidate_embeddings,
    load_job,
    load_job_embeddings,
)
from .filters import passes_hard_filter
from .models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
    MatchItemV2,
    RunMatchingV2Response,
)
from .reasoning import build_reasoning
from .scoring import (
    compute_final_score,
    compute_skills_score,
    cosine_similarity,
    exact_overlap_ratio,
    matched_skills_sorted,
)

_TOP_K_MAX = 10


# ---------------------------------------------------------------------------
# Internal: score one JD↔CV pair
# ---------------------------------------------------------------------------

def _score_pair(
    job: JobPostV2,
    job_emb: Optional[JobEmbeddingsV2],
    cv: CandidateProfileV2,
    cv_emb: Optional[CandidateEmbeddingsV2],
) -> tuple[dict, list[str]]:
    """Compute all score components for one JD↔CV pair.

    Returns:
        scores: dict with title_score, skills_score, req_exp_score,
                req_summary_score, exact_overlap, final_score.
        missing_fields: list of embedding field names that were absent (→ scored 0).
    """
    missing: list[str] = []

    # ---- title ----
    j_title = job_emb.emb_title if job_emb else None
    c_title = cv_emb.emb_title if cv_emb else None
    if j_title is None:
        missing.append("jd.emb_title")
    if c_title is None:
        missing.append("cv.emb_title")
    title_score = cosine_similarity(j_title, c_title)

    # ---- skills (semantic + exact) ----
    j_skills_emb = job_emb.emb_skills if job_emb else None
    c_skills_emb = cv_emb.emb_skills if cv_emb else None
    if j_skills_emb is None:
        missing.append("jd.emb_skills")
    if c_skills_emb is None:
        missing.append("cv.emb_skills")
    semantic_skills = cosine_similarity(j_skills_emb, c_skills_emb)
    exact = exact_overlap_ratio(job.skills, cv.skills)
    blended_skills = compute_skills_score(semantic_skills, exact)

    # ---- requirement↔experience ----
    j_req = job_emb.emb_requirement if job_emb else None
    c_exp = cv_emb.emb_experience if cv_emb else None
    if j_req is None:
        missing.append("jd.emb_requirement")
    if c_exp is None:
        missing.append("cv.emb_experience")
    req_exp_score = cosine_similarity(j_req, c_exp)

    # ---- requirement↔summary ----
    c_sum = cv_emb.emb_summary if cv_emb else None
    if c_sum is None:
        missing.append("cv.emb_summary")
    # j_req may already be in missing; deduplicate at the end
    req_summary_score = cosine_similarity(j_req, c_sum)

    # Deduplicate while preserving insertion order
    missing = list(dict.fromkeys(missing))

    scores = {
        "title_score": title_score,
        "skills_score": blended_skills,
        "req_exp_score": req_exp_score,
        "req_summary_score": req_summary_score,
        "exact_overlap": exact,
        "final_score": compute_final_score(
            title_score, blended_skills, req_exp_score, req_summary_score
        ),
    }
    return scores, missing


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def run_for_job(
    conn: psycopg.Connection,
    job_id: int,
    top_k: int = 10,
    min_score: float = 0.7,
) -> RunMatchingV2Response:
    """Run JD → CV matching for job_id.

    Args:
        conn: Active psycopg connection (caller owns lifecycle).
        job_id: Anchor job post ID.
        top_k: Max matches to return (capped at 10).
        min_score: Minimum final_score threshold (0..1).

    Raises:
        ValueError: If job_id is not found in job_posts_v2.
    """
    top_k = min(top_k, _TOP_K_MAX)
    t_total_start = time.perf_counter()

    # Stage 1 — load anchor + candidates
    job = load_job(conn, job_id)
    if job is None:
        raise ValueError(f"job_id {job_id} not found in job_posts_v2")

    job_emb = load_job_embeddings(conn, job_id)
    candidates = load_all_candidates(conn)
    cand_embs = load_all_candidate_embeddings(conn)
    total_candidates = len(candidates)

    # Stage 2 — hard filter
    t_filter_start = time.perf_counter()
    filtered = [cv for cv in candidates if passes_hard_filter(job, cv)]
    t_filter_end = time.perf_counter()
    total_after_filter = len(filtered)

    # Stage 3 — score
    t_score_start = time.perf_counter()
    # Each entry: (cv, scores_dict, missing_fields)
    scored: list[tuple[CandidateProfileV2, dict, list[str]]] = []
    for cv in filtered:
        cv_emb = cand_embs.get(cv.cv_id)
        scores, missing = _score_pair(job, job_emb, cv, cv_emb)
        scored.append((cv, scores, missing))
    t_score_end = time.perf_counter()

    # Stage 4 — rerank + return
    t_sort_start = time.perf_counter()
    # Sort: final_score desc, tie-break cv_id asc (deterministic)
    scored.sort(key=lambda x: (-x[1]["final_score"], x[0].cv_id))
    # Apply min_score then top_k
    scored = [x for x in scored if x[1]["final_score"] >= min_score][:top_k]
    t_sort_end = time.perf_counter()

    matches: list[MatchItemV2] = []
    for rank, (cv, scores, missing) in enumerate(scored, start=1):
        matched = matched_skills_sorted(job.skills, cv.skills)
        reasoning = build_reasoning(
            title_score=scores["title_score"],
            skills_score=scores["skills_score"],
            req_exp_score=scores["req_exp_score"],
            req_summary_score=scores["req_summary_score"],
            matched_skills=matched,
            missing_emb_fields=missing,
        )
        matches.append(
            MatchItemV2(
                rank=rank,
                cv_id=cv.cv_id,
                job_id=job_id,
                final_score=round(scores["final_score"], 6),
                title_score=round(scores["title_score"], 6),
                skills_score=round(scores["skills_score"], 6),
                req_exp_score=round(scores["req_exp_score"], 6),
                req_summary_score=round(scores["req_summary_score"], 6),
                reasoning=reasoning,
            )
        )

    t_total_end = time.perf_counter()

    return RunMatchingV2Response(
        anchor_type="job",
        anchor_id=job_id,
        total_candidates=total_candidates,
        total_after_filter=total_after_filter,
        total_returned=len(matches),
        runtime_ms_total=_ms(t_total_start, t_total_end),
        runtime_ms_filter=_ms(t_filter_start, t_filter_end),
        runtime_ms_scoring=_ms(t_score_start, t_score_end),
        runtime_ms_sort=_ms(t_sort_start, t_sort_end),
        matches=matches,
    )


def run_for_cv(
    conn: psycopg.Connection,
    cv_id: int,
    top_k: int = 10,
    min_score: float = 0.7,
) -> RunMatchingV2Response:
    """Run CV → JD matching for cv_id.

    Args:
        conn: Active psycopg connection (caller owns lifecycle).
        cv_id: Anchor candidate profile ID.
        top_k: Max matches to return (capped at 10).
        min_score: Minimum final_score threshold (0..1).

    Raises:
        ValueError: If cv_id is not found in candidate_profiles_v2.
    """
    top_k = min(top_k, _TOP_K_MAX)
    t_total_start = time.perf_counter()

    # Stage 1 — load anchor + candidates
    cv = load_candidate(conn, cv_id)
    if cv is None:
        raise ValueError(f"cv_id {cv_id} not found in candidate_profiles_v2")

    cv_emb = load_candidate_embeddings(conn, cv_id)
    jobs = load_all_jobs(conn)
    job_embs = load_all_job_embeddings(conn)
    total_candidates = len(jobs)

    # Stage 2 — hard filter (always: job constraints checked against cv)
    t_filter_start = time.perf_counter()
    filtered = [job for job in jobs if passes_hard_filter(job, cv)]
    t_filter_end = time.perf_counter()
    total_after_filter = len(filtered)

    # Stage 3 — score
    t_score_start = time.perf_counter()
    scored: list[tuple[JobPostV2, dict, list[str]]] = []
    for job in filtered:
        job_emb = job_embs.get(job.job_id)
        scores, missing = _score_pair(job, job_emb, cv, cv_emb)
        scored.append((job, scores, missing))
    t_score_end = time.perf_counter()

    # Stage 4 — rerank + return
    t_sort_start = time.perf_counter()
    # Sort: final_score desc, tie-break job_id asc (deterministic)
    scored.sort(key=lambda x: (-x[1]["final_score"], x[0].job_id))
    scored = [x for x in scored if x[1]["final_score"] >= min_score][:top_k]
    t_sort_end = time.perf_counter()

    matches: list[MatchItemV2] = []
    for rank, (job, scores, missing) in enumerate(scored, start=1):
        matched = matched_skills_sorted(job.skills, cv.skills)
        reasoning = build_reasoning(
            title_score=scores["title_score"],
            skills_score=scores["skills_score"],
            req_exp_score=scores["req_exp_score"],
            req_summary_score=scores["req_summary_score"],
            matched_skills=matched,
            missing_emb_fields=missing,
        )
        matches.append(
            MatchItemV2(
                rank=rank,
                cv_id=cv_id,
                job_id=job.job_id,
                final_score=round(scores["final_score"], 6),
                title_score=round(scores["title_score"], 6),
                skills_score=round(scores["skills_score"], 6),
                req_exp_score=round(scores["req_exp_score"], 6),
                req_summary_score=round(scores["req_summary_score"], 6),
                reasoning=reasoning,
            )
        )

    t_total_end = time.perf_counter()

    return RunMatchingV2Response(
        anchor_type="cv",
        anchor_id=cv_id,
        total_candidates=total_candidates,
        total_after_filter=total_after_filter,
        total_returned=len(matches),
        runtime_ms_total=_ms(t_total_start, t_total_end),
        runtime_ms_filter=_ms(t_filter_start, t_filter_end),
        runtime_ms_scoring=_ms(t_score_start, t_score_end),
        runtime_ms_sort=_ms(t_sort_start, t_sort_end),
        matches=matches,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ms(t_start: float, t_end: float) -> float:
    return round((t_end - t_start) * 1000, 2)
