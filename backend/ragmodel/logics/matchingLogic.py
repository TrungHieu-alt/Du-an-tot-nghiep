import numpy as np
import logging
import json
from typing import Dict, List, Optional

from ragmodel.db import vectorStore as vs
from ragmodel.logics.embedder import embed_cv, embed_jd
from ragmodel.logics.llmEvaluate import evaluate_match


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# CONSTANTS
# ============================
class MatchingConfig:
    """Configuration for matching system"""
    # Retrieval stages
    ANN_K = 50
    RERANK_K = 10
    FINAL_K = 5
    
    # Field weights (MVP: skills > experience > summary > job_title > full > location)
    FIELD_WEIGHTS = {
        "skills": 0.30,
        "experience_requirement": 0.25,
        "summary_description": 0.20,
        "job_title": 0.15,
        "full": 0.05,
        "location": 0.05,
    }
    
    # Hybrid scoring weights
    HYBRID_WEIGHTS = {
        "ann": 0.2,
        "weighted": 0.5,
        "llm": 0.3,
    }

# Field mappings between CV and JD
CV_JD_FIELD_MAP = {
    "summary_description": ("emb_summary", "emb_job_description"),
    "experience_requirement": ("emb_experience", "emb_job_requirement"),
    "job_title": ("emb_job_title", "emb_job_title"),
    "skills": ("emb_skills", "emb_skills"),
    "location": ("emb_location", "emb_location"),
    "full": ("emb_full", "emb_full"),
}

# ============================
# Helper: Deserialize embeddings
# ============================
def deserialize_embeddings(embeddings_json: str) -> Dict[str, Optional[np.ndarray]]:
    """
    Deserialize embeddings from JSON string to numpy arrays.
    
    Args:
        embeddings_json: JSON string containing embeddings
        
    Returns:
        Dictionary of numpy arrays (or None for missing embeddings)
    """
    try:
        embeddings_dict = json.loads(embeddings_json)
        return {
            k: np.array(v) if v is not None else None 
            for k, v in embeddings_dict.items()
        }
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to deserialize embeddings: {e}")
        return {}

# ============================
# Cosine similarity helper
# ============================
def cosine(a: Optional[np.ndarray], b: Optional[np.ndarray]) -> float:
    """
    Calculate cosine similarity between two vectors.
    Returns 0.0 if either vector is None or invalid.
    """
    if a is None or b is None:
        return 0.0
    
    # Ensure numpy arrays
    a = np.array(a) if not isinstance(a, np.ndarray) else a
    b = np.array(b) if not isinstance(b, np.ndarray) else b
    
    # Validate shapes
    if len(a) == 0 or len(b) == 0 or a.shape != b.shape:
        return 0.0
    
    # Already normalized in embedder.py, so dot product = cosine similarity
    return float(np.dot(a, b))

# ============================
# Weighted Vector Similarity
# ============================
def calc_weighted_vector_sim(
    cv_emb: Dict[str, np.ndarray], 
    jd_emb: Dict[str, np.ndarray]
) -> float:
    """
    Calculate weighted similarity between CV embeddings and JD embeddings.
    Uses shared FIELD_WEIGHTS and field mappings.
    
    Args:
        cv_emb: Dictionary of CV embeddings with keys like "emb_summary", "emb_skills", etc.
        jd_emb: Dictionary of JD embeddings with keys like "emb_job_description", "emb_skills", etc.
    
    Returns:
        Weighted similarity score [0.0, 1.0]
    """
    scores = {}
    for key, (cv_field, jd_field) in CV_JD_FIELD_MAP.items():
        scores[key] = cosine(cv_emb.get(cv_field), jd_emb.get(jd_field))
    
    weighted_sim = sum(
        scores[key] * MatchingConfig.FIELD_WEIGHTS[key] 
        for key in MatchingConfig.FIELD_WEIGHTS
    )
    
    return weighted_sim

# ============================
# Helper: Normalize LLM score
# ============================
def normalize_llm_score(score: float) -> float:
    """Clamp LLM score to [0, 100] range"""
    try:
        return max(0.0, min(100.0, float(score)))
    except (ValueError, TypeError):
        return 0.0

# ============================
# MATCH JD → CV (Direct matching)
# ============================
def match_jd_to_cv(jd_id: str, cv_id: str) -> Dict:
    """
    Calculate similarity between a specific JD and CV.
    Returns scores for each field and final weighted score.
    
    Args:
        jd_id: Job Description ID
        cv_id: CV ID
    
    Returns:
        Dictionary with cv_id, jd_id, field scores, and final_score
    """
    try:
        # ---- GET CV DATA FROM SINGLE COLLECTION ----
        cv_result = vs.cv_full.get(ids=[cv_id])
        if not cv_result or not cv_result.get("metadatas"):
            logger.error(f"CV {cv_id} not found")
            return {
                "cv_id": cv_id,
                "jd_id": jd_id,
                "scores": {},
                "final_score": 0.0,
            }
        
        # Deserialize embeddings from JSON string
        cv_emb_json = cv_result["metadatas"][0].get("embeddings", "{}")
        cv_vec = deserialize_embeddings(cv_emb_json)
        
        # ---- GET JD DATA FROM SINGLE COLLECTION ----
        jd_result = vs.jd_full.get(ids=[jd_id])
        if not jd_result or not jd_result.get("metadatas"):
            logger.error(f"JD {jd_id} not found")
            return {
                "cv_id": cv_id,
                "jd_id": jd_id,
                "scores": {},
                "final_score": 0.0,
            }
        
        # Deserialize embeddings from JSON string
        jd_emb_json = jd_result["metadatas"][0].get("embeddings", "{}")
        jd_vec = deserialize_embeddings(jd_emb_json)

        # Calculate field-wise scores using consistent mapping
        scores = {}
        for key, (cv_field, jd_field) in CV_JD_FIELD_MAP.items():
            scores[key] = cosine(cv_vec.get(cv_field), jd_vec.get(jd_field))
        
        # Calculate final weighted score
        final_score = sum(
            scores[key] * MatchingConfig.FIELD_WEIGHTS[key] 
            for key in MatchingConfig.FIELD_WEIGHTS
        )

        return {
            "cv_id": cv_id,
            "jd_id": jd_id,
            "scores": scores,
            "final_score": final_score,
        }
        
    except Exception as e:
        logger.error(f"Error fetching vectors for JD {jd_id} and CV {cv_id}: {e}")
        return {
            "cv_id": cv_id,
            "jd_id": jd_id,
            "scores": {},
            "final_score": 0.0,
        }

# ============================
# TOP-K CVs for JD (Retrieval + Rerank)
# ============================
def get_top_k_cvs_for_jd(
    jd_json: Dict, 
    ann_k: int = None, 
    rerank_k: int = None, 
    final_k: int = None
) -> List[Dict]:
    """
    Find top-K CVs matching a Job Description using 3-stage pipeline:
    1. ANN retrieval (broad search)
    2. Weighted vector reranking (precise scoring)
    3. LLM evaluation (reasoning + final ranking)
    
    Args:
        jd_json: Job Description dictionary with fields like job_title, job_description, etc.
        ann_k: Number of candidates from ANN stage (default: 50)
        rerank_k: Number of candidates to send to LLM (default: 10)
        final_k: Number of final results to return (default: 5)
    
    Returns:
        List of top-K CV matches with scores and reasoning
    """
    import time
    start_time = time.time()
    
    # Use config defaults if not specified
    ann_k = ann_k or MatchingConfig.ANN_K
    rerank_k = rerank_k or MatchingConfig.RERANK_K
    final_k = final_k or MatchingConfig.FINAL_K
    
    # Get JD embeddings
    jd_emb = embed_jd(jd_json)

    try:
        # ==== STAGE 1: ANN Retrieval ====
        ann_results = vs.cv_full.query(
            query_embeddings=[jd_emb["emb_full"]],
            n_results=ann_k
        )
        
        if not ann_results or not ann_results.get("ids"):
            logger.warning("No results from ANN query")
            return []
        
        candidate_ids = ann_results["ids"][0]
        candidate_metas = ann_results["metadatas"][0]
        
        logger.info(f"Stage 1 (ANN): Retrieved {len(candidate_ids)} candidates")

        # ==== STAGE 2: Weighted Vector Reranking ====
        candidates = []
        skipped = 0
        
        for cv_id, meta in zip(candidate_ids, candidate_metas):
            # Deserialize embeddings from JSON string
            cv_emb_json = meta.get("embeddings", "{}")
            cv_emb = deserialize_embeddings(cv_emb_json)
            
            if not cv_emb:
                skipped += 1
                logger.debug(f"Skipping CV {cv_id}: no embeddings in metadata")
                continue
            
            # Calculate weighted similarity
            weighted_sim = calc_weighted_vector_sim(cv_emb, jd_emb)
            cosine_ann = cosine(jd_emb["emb_full"], cv_emb.get("emb_full"))

            candidates.append({
                "id": cv_id,
                "cv": meta,
                "cosine_ann": cosine_ann,
                "weighted_sim": weighted_sim
            })
        
        if skipped > 0:
            logger.warning(f"Skipped {skipped} candidates due to missing embeddings")

        # Sort by weighted similarity and take top for LLM
        candidates.sort(key=lambda x: x["weighted_sim"], reverse=True)
        top_for_llm = candidates[:rerank_k]
        
        logger.info(f"Stage 2 (Weighted): Reranked to top {len(top_for_llm)} candidates")

        # ==== STAGE 3: LLM Evaluation ====
        for c in top_for_llm:
            try:
                # Call LLM with JD first, then CV
                llm_result = evaluate_match(
                    jd_json.get("full_text", ""), 
                    c["cv"].get("full_text", "")
                )
                
                # Normalize and store LLM score
                c["llm_score"] = normalize_llm_score(llm_result.get("score", 0))
                c["reason"] = llm_result.get("reason", "")
                time.sleep(1)  # To avoid rate limits
            except Exception as e:
                logger.warning(f"LLM evaluation failed for CV {c['id']}: {e}")
                # Fallback: use weighted similarity as proxy
                c["llm_score"] = c["weighted_sim"] * 100
                c["reason"] = "LLM evaluation unavailable (using vector similarity)"

        logger.info(f"Stage 3 (LLM): Evaluated {len(top_for_llm)} candidates")

        # ==== STAGE 4: Hybrid Ranking ====
        def calculate_final_score(candidate: Dict) -> float:
            """Calculate final hybrid score (all normalized to [0,1])"""
            return (
                MatchingConfig.HYBRID_WEIGHTS["ann"] * candidate["cosine_ann"] +
                MatchingConfig.HYBRID_WEIGHTS["weighted"] * candidate["weighted_sim"] +
                MatchingConfig.HYBRID_WEIGHTS["llm"] * (candidate.get("llm_score", 0) / 100)
            )

        # Sort by final hybrid score
        top_for_llm.sort(key=calculate_final_score, reverse=True)
        final_results = top_for_llm[:final_k]
        
        # Log completion
        elapsed = time.time() - start_time
        logger.info(
            f"Matching completed in {elapsed:.2f}s: "
            f"ANN({len(candidate_ids)}) → Weighted({len(top_for_llm)}) → Final({len(final_results)})"
        )

        return final_results
        
    except Exception as e:
        logger.error(f"Error in get_top_k_cvs_for_jd: {e}", exc_info=True)
        return []

# ============================
# TOP-K JDs for CV (Retrieval + Rerank)
# ============================
def get_top_k_jds_for_cv(
    cv_json: Dict, 
    ann_k: int = None, 
    rerank_k: int = None, 
    final_k: int = None
) -> List[Dict]:
    """
    Find top-K Job Descriptions matching a CV using 3-stage pipeline:
    1. ANN retrieval (broad search)
    2. Weighted vector reranking (precise scoring)
    3. LLM evaluation (reasoning + final ranking)
    
    Args:
        cv_json: CV dictionary with fields like job_title, summary, experience, etc.
        ann_k: Number of candidates from ANN stage (default: 50)
        rerank_k: Number of candidates to send to LLM (default: 10)
        final_k: Number of final results to return (default: 5)
    
    Returns:
        List of top-K JD matches with scores and reasoning
    """
    import time
    start_time = time.time()
    
    # Use config defaults if not specified
    ann_k = ann_k or MatchingConfig.ANN_K
    rerank_k = rerank_k or MatchingConfig.RERANK_K
    final_k = final_k or MatchingConfig.FINAL_K
    
    # Get CV embeddings
    cv_emb = embed_cv(cv_json)

    try:
        # ==== STAGE 1: ANN Retrieval ====
        ann_results = vs.jd_full.query(
            query_embeddings=[cv_emb["emb_full"]],
            n_results=ann_k
        )
        
        if not ann_results or not ann_results.get("ids"):
            logger.warning("No results from ANN query")
            return []
        
        candidate_ids = ann_results["ids"][0]
        candidate_metas = ann_results["metadatas"][0]
        
        logger.info(f"Stage 1 (ANN): Retrieved {len(candidate_ids)} candidates")

        # ==== STAGE 2: Weighted Vector Reranking ====
        candidates = []
        skipped = 0
        
        for jd_id, meta in zip(candidate_ids, candidate_metas):
            # Deserialize embeddings from JSON string
            jd_emb_json = meta.get("embeddings", "{}")
            jd_emb = deserialize_embeddings(jd_emb_json)
            
            if not jd_emb:
                skipped += 1
                logger.debug(f"Skipping JD {jd_id}: no embeddings in metadata")
                continue
            
            # Calculate weighted similarity
            weighted_sim = calc_weighted_vector_sim(cv_emb, jd_emb)
            cosine_ann = cosine(cv_emb["emb_full"], jd_emb.get("emb_full"))

            candidates.append({
                "id": jd_id,
                "jd": meta,
                "cosine_ann": cosine_ann,
                "weighted_sim": weighted_sim
            })
        
        if skipped > 0:
            logger.warning(f"Skipped {skipped} candidates due to missing embeddings")

        # Sort by weighted similarity and take top for LLM
        candidates.sort(key=lambda x: x["weighted_sim"], reverse=True)
        top_for_llm = candidates[:rerank_k]
        
        logger.info(f"Stage 2 (Weighted): Reranked to top {len(top_for_llm)} candidates")

        # ==== STAGE 3: LLM Evaluation ====
        for c in top_for_llm:
            try:
                # Call LLM with JD first, then CV
                llm_result = evaluate_match(
                    c["jd"].get("full_text", ""), 
                    cv_json.get("full_text", "")
                )
                
                # Normalize and store LLM score
                c["llm_score"] = normalize_llm_score(llm_result.get("score", 0))
                c["reason"] = llm_result.get("reason", "")
                
            except Exception as e:
                logger.warning(f"LLM evaluation failed for JD {c['id']}: {e}")
                # Fallback: use weighted similarity as proxy
                c["llm_score"] = c["weighted_sim"] * 100
                c["reason"] = "LLM evaluation unavailable (using vector similarity)"

        logger.info(f"Stage 3 (LLM): Evaluated {len(top_for_llm)} candidates")

        # ==== STAGE 4: Hybrid Ranking ====
        def calculate_final_score(candidate: Dict) -> float:
            """Calculate final hybrid score (all normalized to [0,1])"""
            return (
                MatchingConfig.HYBRID_WEIGHTS["ann"] * candidate["cosine_ann"] +
                MatchingConfig.HYBRID_WEIGHTS["weighted"] * candidate["weighted_sim"] +
                MatchingConfig.HYBRID_WEIGHTS["llm"] * (candidate.get("llm_score", 0) / 100)
            )

        # Sort by final hybrid score
        top_for_llm.sort(key=calculate_final_score, reverse=True)
        final_results = top_for_llm[:final_k]
        
        # Log completion
        elapsed = time.time() - start_time
        logger.info(
            f"Matching completed in {elapsed:.2f}s: "
            f"ANN({len(candidate_ids)}) → Weighted({len(top_for_llm)}) → Final({len(final_results)})"
        )

        return final_results
        
    except Exception as e:
        logger.error(f"Error in get_top_k_jds_for_cv: {e}", exc_info=True)
        return []