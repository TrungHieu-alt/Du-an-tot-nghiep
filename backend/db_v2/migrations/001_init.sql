-- Matching V2 Prototype (Run-Only) — schema migration
-- Source of truth: docs/REQUIREMENTS.md sections 5.1, 5.2, 5.3, 9.
-- Scope lock: only the 4 prototype tables. No match_results_v2.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE candidate_profiles_v2 (
    cv_id          BIGINT PRIMARY KEY,
    title          TEXT NOT NULL,
    skills         TEXT[] NOT NULL DEFAULT '{}',
    summary        TEXT NOT NULL DEFAULT '',
    experience     TEXT NOT NULL DEFAULT '',
    location       TEXT NOT NULL,
    job_type       TEXT NOT NULL,
    seniority      TEXT NOT NULL,
    education      TEXT NOT NULL,
    certifications TEXT[] NOT NULL DEFAULT '{}',
    CONSTRAINT candidate_profiles_v2_location_chk
        CHECK (location IN ('Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng')),
    CONSTRAINT candidate_profiles_v2_job_type_chk
        CHECK (job_type IN ('remote', 'fulltime', 'parttime')),
    CONSTRAINT candidate_profiles_v2_seniority_chk
        CHECK (seniority IN ('intern', 'fresher', 'junior', 'mid', 'senior', 'lead')),
    CONSTRAINT candidate_profiles_v2_education_chk
        CHECK (education IN ('high_school', 'bachelor', 'master', 'phd'))
);

CREATE TABLE job_posts_v2 (
    job_id                  BIGINT PRIMARY KEY,
    title                   TEXT NOT NULL,
    skills                  TEXT[] NOT NULL DEFAULT '{}',
    requirement             TEXT NOT NULL DEFAULT '',
    location                TEXT NOT NULL,
    job_type                TEXT NOT NULL,
    seniority               TEXT NOT NULL,
    education               TEXT NOT NULL,
    required_certifications TEXT[] NOT NULL DEFAULT '{}',
    CONSTRAINT job_posts_v2_location_chk
        CHECK (location IN ('Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng')),
    CONSTRAINT job_posts_v2_job_type_chk
        CHECK (job_type IN ('remote', 'fulltime', 'parttime')),
    CONSTRAINT job_posts_v2_seniority_chk
        CHECK (seniority IN ('intern', 'fresher', 'junior', 'mid', 'senior', 'lead')),
    CONSTRAINT job_posts_v2_education_chk
        CHECK (education IN ('high_school', 'bachelor', 'master', 'phd'))
);

-- Embeddings live in separate tables so a missing embedding does not bloat the
-- profile/job row. Per REQUIREMENTS.md §9, a missing embedding scores 0 — so
-- columns are nullable.
CREATE TABLE candidate_embeddings_v2 (
    cv_id          BIGINT PRIMARY KEY
                       REFERENCES candidate_profiles_v2(cv_id) ON DELETE CASCADE,
    emb_title      VECTOR(384),
    emb_skills     VECTOR(384),
    emb_summary    VECTOR(384),
    emb_experience VECTOR(384)
);

CREATE TABLE job_embeddings_v2 (
    job_id          BIGINT PRIMARY KEY
                        REFERENCES job_posts_v2(job_id) ON DELETE CASCADE,
    emb_title       VECTOR(384),
    emb_skills      VECTOR(384),
    emb_requirement VECTOR(384)
);
