from __future__ import annotations

import time
from typing import Any, Optional

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
    MatchingScoreBreakdown,
)
from jobconnect.modules.resumes.service import RESUME_DETAIL_COLS, get_resume_row, resume_summary


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
        "final_score": compute_final_score(title, skills, req_exp, req_summary),
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


def _run_matching(anchor_type: str, anchor_id: int, request: MatchingRequest) -> MatchingResponse:
    start = time.perf_counter()
    if anchor_type == "job":
        anchor = _load_job(anchor_id)
        with _api().get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {RESUME_DETAIL_COLS} FROM candidate_resumes WHERE status = 'active' ORDER BY resume_id ASC")
            candidates = [_load_resume(r[0]) for r in cur.fetchall()]
        scored = []
        for candidate in candidates:
            if candidate and passes_hard_filter(anchor["model"], candidate["model"]):
                scores, missing = _score_pair(anchor["model"], anchor["emb"], candidate["model"], candidate["emb"])
                scored.append((candidate, scores, missing))
        scored.sort(key=lambda x: (-x[1]["final_score"], x[0]["model"].cv_id))
        scored = [x for x in scored if x[1]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                resume=candidate["summary"],
                final_score=round(scores["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(
                    **{k: round(scores[k], 6) for k in ("title_sim", "skills_sim", "req_exp_sim", "req_summary_sim")}
                ),
                exact_skill_overlap=matched_skills_sorted(anchor["model"].skills, candidate["model"].skills),
                hard_filter_notes=_hard_filter_notes(anchor["model"]),
                reasoning=build_reasoning(
                    title_score=scores["title_sim"],
                    skills_score=scores["skills_sim"],
                    req_exp_score=scores["req_exp_sim"],
                    req_summary_score=scores["req_summary_sim"],
                    matched_skills=matched_skills_sorted(anchor["model"].skills, candidate["model"].skills),
                    missing_emb_fields=missing,
                ),
                missing_embedding_notes=missing,
            )
            for i, (candidate, scores, missing) in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "job", "job_id": anchor_id, "status": anchor["status"]}
    else:
        anchor = _load_resume(anchor_id)
        with _api().get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {JOB_DETAIL_COLS} FROM job_posts WHERE status = 'published' ORDER BY job_id ASC")
            candidates = [_load_job(r[0]) for r in cur.fetchall()]
        scored = []
        for candidate in candidates:
            if candidate and passes_hard_filter(candidate["model"], anchor["model"]):
                scores, missing = _score_pair(candidate["model"], candidate["emb"], anchor["model"], anchor["emb"])
                scored.append((candidate, scores, missing))
        scored.sort(key=lambda x: (-x[1]["final_score"], x[0]["model"].job_id))
        scored = [x for x in scored if x[1]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                job=candidate["summary"],
                final_score=round(scores["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(
                    **{k: round(scores[k], 6) for k in ("title_sim", "skills_sim", "req_exp_sim", "req_summary_sim")}
                ),
                exact_skill_overlap=matched_skills_sorted(candidate["model"].skills, anchor["model"].skills),
                hard_filter_notes=_hard_filter_notes(candidate["model"]),
                reasoning=build_reasoning(
                    title_score=scores["title_sim"],
                    skills_score=scores["skills_sim"],
                    req_exp_score=scores["req_exp_sim"],
                    req_summary_score=scores["req_summary_sim"],
                    matched_skills=matched_skills_sorted(candidate["model"].skills, anchor["model"].skills),
                    missing_emb_fields=missing,
                ),
                missing_embedding_notes=missing,
            )
            for i, (candidate, scores, missing) in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "resume", "resume_id": anchor_id, "status": anchor["status"]}
    return MatchingResponse(
        anchor=anchor_payload,
        items=items,
        runtime={"total_ms": round((time.perf_counter() - start) * 1000, 2), "rerank_ms": 0.0},
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
