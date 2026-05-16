from __future__ import annotations

import time
from typing import Any, Optional

from jobconnect.integrations.rerank import RerankError, get_rerank_provider
from jobconnect.modules.api.shared import CurrentUser, business_error
from jobconnect.modules.jobs.service import JOB_DETAIL_COLS, get_job_row, job_summary
from jobconnect.modules.matching.filters import passes_hard_filter
from jobconnect.modules.matching.models import (
    CandidateEmbeddings,
    CandidateProfileMatch,
    JobEmbeddings,
    JobPostMatch,
)
from jobconnect.modules.matching.reasoning import build_reasoning
from jobconnect.modules.matching.scoring import (
    compute_final_score,
    compute_skills_score,
    cosine_similarity,
    exact_overlap_ratio,
    matched_skills_sorted,
)
from jobconnect.modules.matching.schemas import (
    MatchingItem,
    MatchingRequest,
    MatchingResponse,
    MatchingRuntime,
    MatchingScoreBreakdown,
)
from jobconnect.modules.resumes.service import RESUME_DETAIL_COLS, get_resume_row, resume_summary

RERANK_TOP_N = 10
RERANK_BLEND_DETERMINISTIC = 0.3
RERANK_BLEND_CROSS_ENCODER = 0.7


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def _row_to_job_model(row: tuple) -> JobPostMatch:
    return JobPostMatch(
        job_id=row[0],
        title=row[3],
        skills=tuple(row[5] or []),
        requirement=row[4],
        location=row[6],
        job_type=row[7],
        seniority=row[8],
        education=row[9],
        required_certifications=tuple(row[10] or []),
    )


def _row_to_cv_model(row: tuple) -> CandidateProfileMatch:
    return CandidateProfileMatch(
        cv_id=row[0],
        title=row[2],
        skills=tuple(row[5] or []),
        summary=row[3],
        experience=row[4],
        location=row[6],
        job_type=row[7],
        seniority=row[8],
        education=row[9],
        certifications=tuple(row[10] or []),
    )


def _parse_vec(value: Optional[str]) -> Optional[list[float]]:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return [float(x) for x in stripped.strip("[]").split(",")]


def _load_job(job_id: int) -> Optional[dict[str, Any]]:
    row = get_job_row(job_id)
    if row is None:
        return None
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT emb_title::text, emb_skills::text, emb_requirement::text FROM job_post_embeddings WHERE job_id = %s",
            (job_id,),
        )
        emb = cur.fetchone()
    return {
        "row": row,
        "model": _row_to_job_model(row),
        "summary": job_summary((row[0], row[3], row[6], row[7], row[8], row[9], row[5], row[10], row[11], row[12])),
        "status": row[11],
        "emb": JobEmbeddings(job_id, _parse_vec(emb[0]), _parse_vec(emb[1]), _parse_vec(emb[2])) if emb else None,
    }


def _load_resume(resume_id: int) -> Optional[dict[str, Any]]:
    row = get_resume_row(resume_id)
    if row is None:
        return None
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT emb_title::text, emb_skills::text, emb_summary::text, emb_experience::text FROM candidate_resume_embeddings WHERE resume_id = %s",
            (resume_id,),
        )
        emb = cur.fetchone()
    return {
        "row": row,
        "model": _row_to_cv_model(row),
        "summary": resume_summary((row[0], row[2], row[6], row[7], row[8], row[9], row[5], row[10], row[12])),
        "status": row[12],
        "emb": CandidateEmbeddings(resume_id, _parse_vec(emb[0]), _parse_vec(emb[1]), _parse_vec(emb[2]), _parse_vec(emb[3])) if emb else None,
    }


def _score_pair(
    job: JobPostMatch,
    job_emb: Optional[JobEmbeddings],
    cv: CandidateProfileMatch,
    cv_emb: Optional[CandidateEmbeddings],
):
    missing: list[str] = []
    if not job_emb or job_emb.emb_title is None:
        missing.append("job.emb_title")
    if not cv_emb or cv_emb.emb_title is None:
        missing.append("resume.emb_title")
    title = cosine_similarity(job_emb.emb_title if job_emb else None, cv_emb.emb_title if cv_emb else None)
    if not job_emb or job_emb.emb_skills is None:
        missing.append("job.emb_skills")
    if not cv_emb or cv_emb.emb_skills is None:
        missing.append("resume.emb_skills")
    semantic_skills = cosine_similarity(job_emb.emb_skills if job_emb else None, cv_emb.emb_skills if cv_emb else None)
    exact = exact_overlap_ratio(job.skills, cv.skills)
    skills = compute_skills_score(semantic_skills, exact)
    if not job_emb or job_emb.emb_requirement is None:
        missing.append("job.emb_requirement")
    if not cv_emb or cv_emb.emb_experience is None:
        missing.append("resume.emb_experience")
    req_exp = cosine_similarity(job_emb.emb_requirement if job_emb else None, cv_emb.emb_experience if cv_emb else None)
    if not cv_emb or cv_emb.emb_summary is None:
        missing.append("resume.emb_summary")
    req_summary = cosine_similarity(job_emb.emb_requirement if job_emb else None, cv_emb.emb_summary if cv_emb else None)
    return {
        "title_sim": title,
        "skills_sim": skills,
        "req_exp_sim": req_exp,
        "req_summary_sim": req_summary,
        "exact": exact,
        "bonus_exact_skill": 0.0,
        "penalty_missing_required": 0.0,
        "deterministic_score": compute_final_score(title, skills, req_exp, req_summary),
    }, list(dict.fromkeys(missing))


def _hard_filter_notes(job: JobPostMatch) -> list[str]:
    notes = ["job_type matched", "seniority matched", "education requirement satisfied"]
    if job.job_type == "remote":
        notes.append("remote job skips location hard filter")
    else:
        notes.append("location matched")
    if job.required_certifications:
        notes.append("required certifications satisfied")
    return notes


def _candidate_text_for_rerank(anchor_type: str, anchor: dict[str, Any], candidate: dict[str, Any]) -> tuple[str, str]:
    if anchor_type == "job":
        query = f"{anchor['model'].title}\n{anchor['model'].requirement}\n{' '.join(anchor['model'].skills)}"
        document = (
            f"{candidate['model'].title}\n"
            f"{candidate['model'].summary}\n"
            f"{candidate['model'].experience}\n"
            f"{' '.join(candidate['model'].skills)}"
        )
    else:
        query = (
            f"{anchor['model'].title}\n"
            f"{anchor['model'].summary}\n"
            f"{anchor['model'].experience}\n"
            f"{' '.join(anchor['model'].skills)}"
        )
        document = f"{candidate['model'].title}\n{candidate['model'].requirement}\n{' '.join(candidate['model'].skills)}"
    return query.strip(), document.strip()


def _blend_scores(deterministic_score: float, rerank_score: float) -> float:
    return (
        RERANK_BLEND_DETERMINISTIC * deterministic_score
        + RERANK_BLEND_CROSS_ENCODER * rerank_score
    )


def _run_matching(anchor_type: str, anchor_id: int, request: MatchingRequest) -> MatchingResponse:
    started = time.perf_counter()
    warnings: list[str] = []
    rerank_applied = False
    retrieval_ms = 0.0
    filter_ms = 0.0
    scoring_ms = 0.0
    rerank_ms = 0.0

    if anchor_type == "job":
        anchor = _load_job(anchor_id)
        retrieve_start = time.perf_counter()
        with _api().get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {RESUME_DETAIL_COLS} FROM candidate_resumes WHERE status = 'active' ORDER BY resume_id ASC")
            candidates = [_load_resume(r[0]) for r in cur.fetchall()]
        retrieval_ms = (time.perf_counter() - retrieve_start) * 1000

        filter_start = time.perf_counter()
        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate and passes_hard_filter(anchor["model"], candidate["model"])
        ]
        filter_ms = (time.perf_counter() - filter_start) * 1000

        score_start = time.perf_counter()
        scored: list[dict[str, Any]] = []
        for candidate in filtered_candidates:
            scores, missing = _score_pair(anchor["model"], anchor["emb"], candidate["model"], candidate["emb"])
            scored.append(
                {
                    "candidate": candidate,
                    "scores": scores,
                    "missing": missing,
                    "rerank_score": None,
                }
            )
        scored.sort(key=lambda x: (-x["scores"]["deterministic_score"], x["candidate"]["model"].cv_id))
        scoring_ms = (time.perf_counter() - score_start) * 1000

        rerank_start = time.perf_counter()
        rerank_target = scored[:RERANK_TOP_N]
        if rerank_target:
            query_docs = [_candidate_text_for_rerank(anchor_type, anchor, item["candidate"]) for item in rerank_target]
            query = query_docs[0][0]
            docs = [doc for _, doc in query_docs]
            try:
                rerank_scores = get_rerank_provider().score(query, docs)
                for item, rerank_score in zip(rerank_target, rerank_scores):
                    item["rerank_score"] = rerank_score
                    item["scores"]["final_score"] = _blend_scores(item["scores"]["deterministic_score"], rerank_score)
                rerank_applied = True
            except RerankError as exc:
                warnings.append(f"rerank_fallback: {exc}")
                for item in rerank_target:
                    item["scores"]["final_score"] = item["scores"]["deterministic_score"]
            except Exception as exc:  # pragma: no cover
                warnings.append(f"rerank_fallback: {exc}")
                for item in rerank_target:
                    item["scores"]["final_score"] = item["scores"]["deterministic_score"]
        rerank_ms = (time.perf_counter() - rerank_start) * 1000

        for item in scored[RERANK_TOP_N:]:
            item["scores"]["final_score"] = item["scores"]["deterministic_score"]

        scored.sort(key=lambda x: (-x["scores"]["final_score"], x["candidate"]["model"].cv_id))
        filtered_total = len(scored)
        scored = [x for x in scored if x["scores"]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                resume=item["candidate"]["summary"],
                final_score=round(item["scores"]["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(
                    title_sim=round(item["scores"]["title_sim"], 6),
                    skills_sim=round(item["scores"]["skills_sim"], 6),
                    req_exp_sim=round(item["scores"]["req_exp_sim"], 6),
                    req_summary_sim=round(item["scores"]["req_summary_sim"], 6),
                    bonus_exact_skill=round(item["scores"]["bonus_exact_skill"], 6),
                    penalty_missing_required=round(item["scores"]["penalty_missing_required"], 6),
                ),
                exact_skill_overlap=matched_skills_sorted(anchor["model"].skills, item["candidate"]["model"].skills),
                hard_filter_notes=_hard_filter_notes(anchor["model"]),
                reasoning=build_reasoning(
                    title_score=item["scores"]["title_sim"],
                    skills_score=item["scores"]["skills_sim"],
                    req_exp_score=item["scores"]["req_exp_sim"],
                    req_summary_score=item["scores"]["req_summary_sim"],
                    matched_skills=matched_skills_sorted(anchor["model"].skills, item["candidate"]["model"].skills),
                    missing_emb_fields=item["missing"],
                ),
                missing_embedding_notes=item["missing"],
            )
            for i, item in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "job", "job_id": anchor_id, "status": anchor["status"]}
        candidates_total = len(candidates)
    else:
        anchor = _load_resume(anchor_id)
        retrieve_start = time.perf_counter()
        with _api().get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {JOB_DETAIL_COLS} FROM job_posts WHERE status = 'published' ORDER BY job_id ASC")
            candidates = [_load_job(r[0]) for r in cur.fetchall()]
        retrieval_ms = (time.perf_counter() - retrieve_start) * 1000

        filter_start = time.perf_counter()
        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate and passes_hard_filter(candidate["model"], anchor["model"])
        ]
        filter_ms = (time.perf_counter() - filter_start) * 1000

        score_start = time.perf_counter()
        scored: list[dict[str, Any]] = []
        for candidate in filtered_candidates:
            scores, missing = _score_pair(candidate["model"], candidate["emb"], anchor["model"], anchor["emb"])
            scored.append(
                {
                    "candidate": candidate,
                    "scores": scores,
                    "missing": missing,
                    "rerank_score": None,
                }
            )
        scored.sort(key=lambda x: (-x["scores"]["deterministic_score"], x["candidate"]["model"].job_id))
        scoring_ms = (time.perf_counter() - score_start) * 1000

        rerank_start = time.perf_counter()
        rerank_target = scored[:RERANK_TOP_N]
        if rerank_target:
            query_docs = [_candidate_text_for_rerank(anchor_type, anchor, item["candidate"]) for item in rerank_target]
            query = query_docs[0][0]
            docs = [doc for _, doc in query_docs]
            try:
                rerank_scores = get_rerank_provider().score(query, docs)
                for item, rerank_score in zip(rerank_target, rerank_scores):
                    item["rerank_score"] = rerank_score
                    item["scores"]["final_score"] = _blend_scores(item["scores"]["deterministic_score"], rerank_score)
                rerank_applied = True
            except RerankError as exc:
                warnings.append(f"rerank_fallback: {exc}")
                for item in rerank_target:
                    item["scores"]["final_score"] = item["scores"]["deterministic_score"]
            except Exception as exc:  # pragma: no cover
                warnings.append(f"rerank_fallback: {exc}")
                for item in rerank_target:
                    item["scores"]["final_score"] = item["scores"]["deterministic_score"]
        rerank_ms = (time.perf_counter() - rerank_start) * 1000

        for item in scored[RERANK_TOP_N:]:
            item["scores"]["final_score"] = item["scores"]["deterministic_score"]

        scored.sort(key=lambda x: (-x["scores"]["final_score"], x["candidate"]["model"].job_id))
        filtered_total = len(scored)
        scored = [x for x in scored if x["scores"]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                job=item["candidate"]["summary"],
                final_score=round(item["scores"]["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(
                    title_sim=round(item["scores"]["title_sim"], 6),
                    skills_sim=round(item["scores"]["skills_sim"], 6),
                    req_exp_sim=round(item["scores"]["req_exp_sim"], 6),
                    req_summary_sim=round(item["scores"]["req_summary_sim"], 6),
                    bonus_exact_skill=round(item["scores"]["bonus_exact_skill"], 6),
                    penalty_missing_required=round(item["scores"]["penalty_missing_required"], 6),
                ),
                exact_skill_overlap=matched_skills_sorted(item["candidate"]["model"].skills, anchor["model"].skills),
                hard_filter_notes=_hard_filter_notes(item["candidate"]["model"]),
                reasoning=build_reasoning(
                    title_score=item["scores"]["title_sim"],
                    skills_score=item["scores"]["skills_sim"],
                    req_exp_score=item["scores"]["req_exp_sim"],
                    req_summary_score=item["scores"]["req_summary_sim"],
                    matched_skills=matched_skills_sorted(item["candidate"]["model"].skills, anchor["model"].skills),
                    missing_emb_fields=item["missing"],
                ),
                missing_embedding_notes=item["missing"],
            )
            for i, item in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "resume", "resume_id": anchor_id, "status": anchor["status"]}
        candidates_total = len(candidates)

    total_ms = (time.perf_counter() - started) * 1000
    return MatchingResponse(
        anchor=anchor_payload,
        items=items,
        runtime=MatchingRuntime(
            total_ms=round(total_ms, 2),
            retrieval_ms=round(retrieval_ms, 2),
            filter_ms=round(filter_ms, 2),
            scoring_ms=round(scoring_ms, 2),
            rerank_ms=round(rerank_ms, 2),
            candidates_total=candidates_total,
            candidates_after_filter=filtered_total,
            rerank_applied=rerank_applied,
            warnings=warnings,
        ),
    )


def run_job_matching(job_id: int, request: MatchingRequest, user: CurrentUser) -> MatchingResponse:
    job = _load_job(job_id)
    if job is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and job["row"][2] != user.user_id:
        raise business_error(403, "forbidden", "You can match only against your own jobs.")
    if job["status"] != "published":
        raise business_error(400, "invalid_anchor", "Job anchor must be published.")
    return _run_matching("job", job_id, request)


def run_resume_matching(resume_id: int, request: MatchingRequest, user: CurrentUser) -> MatchingResponse:
    resume = _load_resume(resume_id)
    if resume is None:
        raise business_error(404, "not_found", "Resume not found.")
    if user.role == "candidate" and resume["row"][1] != user.user_id:
        raise business_error(403, "forbidden", "You can match only against your own resumes.")
    if resume["status"] != "active":
        raise business_error(400, "invalid_anchor", "Resume anchor must be active.")
    return _run_matching("resume", resume_id, request)
