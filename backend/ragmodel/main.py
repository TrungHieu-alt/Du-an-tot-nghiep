import sys
from dataPreprocess.resumePreprocess import preprocess_resume
from dataPreprocess.resumeParser import parse_resume
from dataPreprocess.jobPreprocess import preprocess_jd
from dataPreprocess.jobParser import parse_jd
from logics.embedder import embed_cv, embed_jd
from db.vectorStore import store_cv, store_jd
from logics.matchingLogic import match_jd_to_cvs

import uuid


# ----------------------------------------
# Helpers
# ----------------------------------------
def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


# ----------------------------------------
# MAIN TEST PIPELINE
# ----------------------------------------
def run_test(cv_path, jd_path):
    print_section("▶ 1. READING + PREPROCESS RESUME")
    cv_blocks = preprocess_resume(cv_path)
    print(cv_blocks[:300] + "..." if len(cv_blocks) > 300 else cv_blocks)

    print_section("▶ 2. PARSE RESUME")
    cv_json = parse_resume(cv_blocks)
    print(cv_json)

    print_section("▶ 3. READING + PREPROCESS JOB DESCRIPTION")
    jd_blocks = preprocess_jd(jd_path)
    print(jd_blocks[:300] + "..." if len(jd_blocks) > 300 else jd_blocks)

    print_section("▶ 4. PARSE JOB")
    jd_json = parse_jd(jd_blocks)
    print(jd_json)

    print_section("▶ 5. EMBEDDING CV")
    cv_emb = embed_cv(cv_json)

    print_section("▶ 6. EMBEDDING JD")
    jd_emb = embed_jd(jd_json)

    print_section("▶ 7. STORE IN VECTOR DB (10 collections)")
    cv_id = "cv_" + str(uuid.uuid4())
    jd_id = "jd_" + str(uuid.uuid4())

    store_cv(cv_id, cv_emb)
    store_jd(jd_id, jd_emb)

    print("Stored CV ID:", cv_id)
    print("Stored JD ID:", jd_id)

    print_section("▶ 8. MATCH: JD → CV LIST (self-test with 1 CV)")
    results = match_jd_to_cvs(jd_json, [cv_json], top_k=1)

    top = results[0]
    print("\n===== MATCH RESULT =====")
    print("Similarity:", round(top["similarity"], 4))
    print("LLM Score:", top["llm_score"])
    print("FINAL SCORE:", round(top["similarity"]*0.6 + top["llm_score"]/100*0.4, 4))
    print("\nReason:")
    print(top["reason"])
    print("========================\n")


# ----------------------------------------
# CLI ENTRY
# ----------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <cv_file> <jd_file>")
        sys.exit(1)

    cv_file = sys.argv[1]
    jd_file = sys.argv[2]

    run_test(cv_file, jd_file)
