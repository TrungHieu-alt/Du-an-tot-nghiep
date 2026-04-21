import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def emb(text):
    """
    Generate embedding for text.
    Returns None for empty/invalid text to avoid zero-vector noise.
    """
    if not text or not str(text).strip():
        return None
    return model.encode(str(text).strip(), normalize_embeddings=True)


# ============================================
# CV EMBEDDER (new schema)
# ============================================
def embed_cv(cv):
    print("\n========== CV EMBEDDING INPUT ==========")

    summary = cv.get("summary", "")
    experience = cv.get("experience", "")
    job_title = cv.get("job_title", "")
    skills = " ".join(cv.get("skills", [])) if cv.get("skills") else ""
    location = cv.get("location", "")
    full = cv.get("full_text", "")

    print("\n[CV SUMMARY]\n", summary[:200] if summary else "(empty)")
    print("\n[CV EXPERIENCE]\n", experience[:200] if experience else "(empty)")
    print("\n[CV JOB TITLE]\n", job_title)
    print("\n[CV SKILLS]\n", skills[:200] if skills else "(empty)")
    print("\n[CV LOCATION]\n", location)
    print("\n[CV FULL TEXT]\n", full[:800] if full else "(empty)", "...\n")

    return {
        "emb_summary": emb(summary),
        "emb_experience": emb(experience),
        "emb_job_title": emb(job_title),
        "emb_skills": emb(skills),
        "emb_location": emb(location),
        "emb_full": emb(full),
    }


# ============================================
# JD EMBEDDER (new schema)
# ============================================
def embed_jd(jd):
    print("\n========== JD EMBEDDING INPUT ==========")

    job_desc = jd.get("job_description", "")
    job_requirement = jd.get("job_requirement", "")
    job_title = jd.get("job_title", "")
    skills = " ".join(jd.get("skills", [])) if jd.get("skills") else ""
    location = jd.get("location", "")
    full = jd.get("full_text", "")

    print("\n[JD DESCRIPTION]\n", job_desc[:200] if job_desc else "(empty)")
    print("\n[JD REQUIREMENT]\n", job_requirement[:200] if job_requirement else "(empty)")
    print("\n[JD JOB TITLE]\n", job_title)
    print("\n[JD SKILLS]\n", skills[:200] if skills else "(empty)")
    print("\n[JD LOCATION]\n", location)
    print("\n[JD FULL TEXT]\n", full[:800] if full else "(empty)", "...\n")

    return {
        "emb_job_description": emb(job_desc),
        "emb_job_requirement": emb(job_requirement),
        "emb_job_title": emb(job_title),
        "emb_skills": emb(skills),
        "emb_location": emb(location),
        "emb_full": emb(full),
    }