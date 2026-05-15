-- Link normal Job/CV rows to the V2 prototype tables for preparation/sync.
-- This is additive: existing V2 seed/scenario rows remain valid and unlinked.

CREATE SEQUENCE IF NOT EXISTS candidate_profiles_v2_cv_id_seq START WITH 1000000000;
CREATE SEQUENCE IF NOT EXISTS job_posts_v2_job_id_seq START WITH 1000000000;

ALTER TABLE candidate_profiles_v2
    ALTER COLUMN cv_id SET DEFAULT nextval('candidate_profiles_v2_cv_id_seq');

ALTER TABLE job_posts_v2
    ALTER COLUMN job_id SET DEFAULT nextval('job_posts_v2_job_id_seq');

ALTER TABLE candidate_profiles_v2
    ADD COLUMN IF NOT EXISTS normal_cv_id UUID UNIQUE REFERENCES cvs(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS candidate_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS source_language TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS prepared_text TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS prepared_text_en TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS preprocess_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS translation_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS text_quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE job_posts_v2
    ADD COLUMN IF NOT EXISTS normal_job_id UUID UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS recruiter_id UUID REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS source_language TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS prepared_text TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS prepared_text_en TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS preprocess_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS translation_warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS text_quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS candidate_profiles_v2_normal_cv_id_idx
    ON candidate_profiles_v2 (normal_cv_id);
CREATE INDEX IF NOT EXISTS candidate_profiles_v2_candidate_id_idx
    ON candidate_profiles_v2 (candidate_id);
CREATE INDEX IF NOT EXISTS candidate_profiles_v2_source_language_idx
    ON candidate_profiles_v2 (source_language);

CREATE INDEX IF NOT EXISTS job_posts_v2_normal_job_id_idx
    ON job_posts_v2 (normal_job_id);
CREATE INDEX IF NOT EXISTS job_posts_v2_recruiter_id_idx
    ON job_posts_v2 (recruiter_id);
CREATE INDEX IF NOT EXISTS job_posts_v2_source_language_idx
    ON job_posts_v2 (source_language);

CREATE OR REPLACE FUNCTION set_candidate_profiles_v2_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS candidate_profiles_v2_set_updated_at ON candidate_profiles_v2;
CREATE TRIGGER candidate_profiles_v2_set_updated_at
BEFORE UPDATE ON candidate_profiles_v2
FOR EACH ROW
EXECUTE FUNCTION set_candidate_profiles_v2_updated_at();

CREATE OR REPLACE FUNCTION set_job_posts_v2_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS job_posts_v2_set_updated_at ON job_posts_v2;
CREATE TRIGGER job_posts_v2_set_updated_at
BEFORE UPDATE ON job_posts_v2
FOR EACH ROW
EXECUTE FUNCTION set_job_posts_v2_updated_at();
