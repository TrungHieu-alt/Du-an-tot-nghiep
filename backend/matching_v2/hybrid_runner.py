"""Run-only orchestrator for the additive hybrid matcher."""

from __future__ import annotations

import time

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
from .hybrid_models import MatchHybridItem, RunMatchingHybridResponse
from .hybrid_scoring import evaluate_pair_hybrid
from .models import CandidateProfileV2, JobPostV2

_TOP_K_MAX = 10


def _to_match_item(rank: int, pair_result) -> MatchHybridItem:
    return MatchHybridItem(
        rank=rank,
        job_id=pair_result.job_id,
        cv_id=pair_result.cv_id,
        final_score=round(pair_result.final_score, 6),
        passed=pair_result.passed,
        breakdown=pair_result.breakdown,
        skipped_groups=pair_result.skipped_groups,
        failed_filters=pair_result.failed_filters,
        warnings=pair_result.warnings,
        explanations=pair_result.explanations,
    )


def _filter_sort_rank(
    results,
    id_key,
    top_k: int,
    min_score: float,
    include_failed: bool,
) -> list[MatchHybridItem]:
    visible = [
        result
        for result in results
        if result.final_score >= min_score and (include_failed or result.passed)
    ]
    visible.sort(key=lambda item: (-item.final_score, id_key(item)))
    return [
        _to_match_item(rank, result)
        for rank, result in enumerate(visible[:top_k], start=1)
    ]


def run_hybrid_for_job(
    conn: psycopg.Connection,
    job_id: int,
    top_k: int = 10,
    min_score: float = 0.0,
    include_failed: bool = False,
    strict_filters: bool = True,
) -> RunMatchingHybridResponse:
    top_k = min(top_k, _TOP_K_MAX)
    t_total_start = time.perf_counter()

    job = load_job(conn, job_id)
    if job is None:
        raise ValueError(f"job_id {job_id} not found in job_posts_v2")
    job_emb = load_job_embeddings(conn, job_id)
    candidates = load_all_candidates(conn)
    cand_embs = load_all_candidate_embeddings(conn)
    total_candidates = len(candidates)

    t_score_start = time.perf_counter()
    results = [
        evaluate_pair_hybrid(
            job=job,
            job_emb=job_emb,
            cv=cv,
            cv_emb=cand_embs.get(cv.cv_id),
            strict_filters=strict_filters,
        )
        for cv in candidates
    ]
    t_score_end = time.perf_counter()

    t_filter_start = time.perf_counter()
    total_after_filter = sum(1 for result in results if result.passed)
    t_filter_end = time.perf_counter()

    t_sort_start = time.perf_counter()
    matches = _filter_sort_rank(
        results=results,
        id_key=lambda item: item.cv_id,
        top_k=top_k,
        min_score=min_score,
        include_failed=include_failed,
    )
    t_sort_end = time.perf_counter()
    t_total_end = time.perf_counter()

    return RunMatchingHybridResponse(
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


def run_hybrid_for_cv(
    conn: psycopg.Connection,
    cv_id: int,
    top_k: int = 10,
    min_score: float = 0.0,
    include_failed: bool = False,
    strict_filters: bool = True,
) -> RunMatchingHybridResponse:
    top_k = min(top_k, _TOP_K_MAX)
    t_total_start = time.perf_counter()

    cv = load_candidate(conn, cv_id)
    if cv is None:
        raise ValueError(f"cv_id {cv_id} not found in candidate_profiles_v2")
    cv_emb = load_candidate_embeddings(conn, cv_id)
    jobs = load_all_jobs(conn)
    job_embs = load_all_job_embeddings(conn)
    total_candidates = len(jobs)

    t_score_start = time.perf_counter()
    results = [
        evaluate_pair_hybrid(
            job=job,
            job_emb=job_embs.get(job.job_id),
            cv=cv,
            cv_emb=cv_emb,
            strict_filters=strict_filters,
        )
        for job in jobs
    ]
    t_score_end = time.perf_counter()

    t_filter_start = time.perf_counter()
    total_after_filter = sum(1 for result in results if result.passed)
    t_filter_end = time.perf_counter()

    t_sort_start = time.perf_counter()
    matches = _filter_sort_rank(
        results=results,
        id_key=lambda item: item.job_id,
        top_k=top_k,
        min_score=min_score,
        include_failed=include_failed,
    )
    t_sort_end = time.perf_counter()
    t_total_end = time.perf_counter()

    return RunMatchingHybridResponse(
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


def _ms(t_start: float, t_end: float) -> float:
    return round((t_end - t_start) * 1000, 2)
