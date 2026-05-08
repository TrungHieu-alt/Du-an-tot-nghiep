"""
Embedding & Matching Test Script
Usage (inside container): python ragmodel/run_embed_test.py
Saves results to: ragmodel/test_results.json
"""
import sys
import os
import uuid
import json
import time
from datetime import datetime

# Make sure imports work from /app/backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragmodel.dataPreprocess.resumePreprocess import preprocess_resume
from ragmodel.dataPreprocess.resumeParser import parse_resume
from ragmodel.dataPreprocess.jobPreprocess import preprocess_jd
from ragmodel.dataPreprocess.jobParser import parse_jd
from ragmodel.logics.embedder import embed_cv, embed_jd
from ragmodel.db.vectorStore import store_cv, store_jd, cv_full, jd_full
from ragmodel.logics.matchingLogic import get_top_k_cvs_for_jd, get_top_k_jds_for_cv
from ragmodel.config import AI_MODE

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "test_data")
RESULTS_FILE = os.path.join(BASE, "test_results.json")

# ─── Test data files ───────────────────────────────────────────────
CV_FILES = [
    ("cv_backend_001", os.path.join(DATA_DIR, "cv1.txt")),
    ("cv_fullstack_002", os.path.join(DATA_DIR, "cv2.txt")),
    ("cv_dataeng_003", os.path.join(DATA_DIR, "cv3.txt")),
]

JD_FILES = [
    ("jd_backend_001", os.path.join(DATA_DIR, "jd1.txt")),
    ("jd_frontend_002", os.path.join(DATA_DIR, "jd2.txt")),
    ("jd_dataeng_003", os.path.join(DATA_DIR, "jd3.txt")),
]


def banner(msg):
    print(f"\n{'='*60}\n{msg}\n{'='*60}")


# ─── STEP 1: Insert CVs ────────────────────────────────────────────
def insert_cvs():
    banner("STEP 1: INSERT CVs")
    inserted = []
    for cv_id, path in CV_FILES:
        # Clear old record if exists
        try:
            cv_full.delete(ids=[cv_id])
        except Exception:
            pass

        blocks = preprocess_resume(path)
        cv_json = parse_resume(blocks)
        cv_emb = embed_cv(cv_json)
        store_cv(cv_id, cv_emb, cv_json)

        skills = cv_json.get("skills", [])
        print(f"  ✅ {cv_id} | skills: {', '.join(skills[:5])}")
        inserted.append({"id": cv_id, "file": os.path.basename(path), "skills": skills})
    print(f"\nTotal CVs in store: {cv_full.count()}")
    return inserted


# ─── STEP 2: Insert JDs ────────────────────────────────────────────
def insert_jds():
    banner("STEP 2: INSERT JDs")
    inserted = []
    for jd_id, path in JD_FILES:
        try:
            jd_full.delete(ids=[jd_id])
        except Exception:
            pass

        blocks = preprocess_jd(path)
        jd_json = parse_jd(blocks)
        jd_emb = embed_jd(jd_json)
        store_jd(jd_id, jd_emb, jd_json)

        skills = jd_json.get("skills", [])
        print(f"  ✅ {jd_id} | skills: {', '.join(skills[:5])}")
        inserted.append({"id": jd_id, "file": os.path.basename(path), "skills": skills})
    print(f"\nTotal JDs in store: {jd_full.count()}")
    return inserted


# ─── STEP 3: Match JD → top CVs ───────────────────────────────────
def run_jd_to_cv_matching():
    banner("STEP 3: MATCH JD → TOP CVs")
    results = {}
    for jd_id, path in JD_FILES:
        blocks = preprocess_jd(path)
        jd_json = parse_jd(blocks)
        jd_json["job_id"] = jd_id

        t0 = time.time()
        matches = get_top_k_cvs_for_jd(jd_json, ann_k=3, rerank_k=3, final_k=3)
        elapsed = round(time.time() - t0, 2)

        print(f"\n  JD: {jd_id} ({elapsed}s)")
        row = []
        for rank, m in enumerate(matches, 1):
            score = round(
                0.2 * m["cosine_ann"] + 0.5 * m["weighted_sim"] + 0.3 * (m.get("llm_score", 0) / 100),
                4
            )
            print(f"    #{rank} {m['id']} | ann={m['cosine_ann']:.4f} weighted={m['weighted_sim']:.4f} llm={m.get('llm_score',0):.1f} final={score}")
            row.append({
                "rank": rank, "cv_id": m["id"],
                "cosine_ann": round(m["cosine_ann"], 4),
                "weighted_sim": round(m["weighted_sim"], 4),
                "llm_score": round(m.get("llm_score", 0), 1),
                "final_score": score,
                "reason": m.get("reason", "")[:120],
            })
        results[jd_id] = {"matches": row, "elapsed_s": elapsed}
    return results


# ─── STEP 4: Match CV → top JDs ───────────────────────────────────
def run_cv_to_jd_matching():
    banner("STEP 4: MATCH CV → TOP JDs")
    results = {}
    for cv_id, path in CV_FILES:
        blocks = preprocess_resume(path)
        cv_json = parse_resume(blocks)
        cv_json["cv_id"] = cv_id

        t0 = time.time()
        matches = get_top_k_jds_for_cv(cv_json, ann_k=3, rerank_k=3, final_k=3)
        elapsed = round(time.time() - t0, 2)

        print(f"\n  CV: {cv_id} ({elapsed}s)")
        row = []
        for rank, m in enumerate(matches, 1):
            score = round(
                0.2 * m["cosine_ann"] + 0.5 * m["weighted_sim"] + 0.3 * (m.get("llm_score", 0) / 100),
                4
            )
            print(f"    #{rank} {m['id']} | ann={m['cosine_ann']:.4f} weighted={m['weighted_sim']:.4f} llm={m.get('llm_score',0):.1f} final={score}")
            row.append({
                "rank": rank, "jd_id": m["id"],
                "cosine_ann": round(m["cosine_ann"], 4),
                "weighted_sim": round(m["weighted_sim"], 4),
                "llm_score": round(m.get("llm_score", 0), 1),
                "final_score": score,
                "reason": m.get("reason", "")[:120],
            })
        results[cv_id] = {"matches": row, "elapsed_s": elapsed}
    return results


# ─── MAIN ──────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 Embedding & Matching Test | AI_MODE={AI_MODE} | {datetime.now():%Y-%m-%d %H:%M:%S}")

    cv_records = insert_cvs()
    jd_records = insert_jds()
    jd_to_cv = run_jd_to_cv_matching()
    cv_to_jd = run_cv_to_jd_matching()

    output = {
        "run_at": datetime.now().isoformat(),
        "ai_mode": AI_MODE,
        "cv_count": cv_full.count(),
        "jd_count": jd_full.count(),
        "inserted_cvs": cv_records,
        "inserted_jds": jd_records,
        "jd_to_cv_matching": jd_to_cv,
        "cv_to_jd_matching": cv_to_jd,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    banner("✅ TEST COMPLETE")
    print(f"Results saved → {RESULTS_FILE}")
    print(f"CVs inserted : {len(cv_records)}")
    print(f"JDs inserted : {len(jd_records)}")
    print(f"JD→CV tests  : {len(jd_to_cv)}")
    print(f"CV→JD tests  : {len(cv_to_jd)}\n")


if __name__ == "__main__":
    main()
