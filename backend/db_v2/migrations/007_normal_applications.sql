-- Normal application submissions connecting candidate CVs to recruiter jobs.
-- This is separate from Matching V2 and stores no score or recommendation data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS applications (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id         UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    cv_id          UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    candidate_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recruiter_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'submitted',
    cover_letter   TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT applications_status_chk
        CHECK (status IN ('submitted', 'reviewing', 'shortlisted', 'rejected', 'accepted', 'withdrawn')),
    CONSTRAINT applications_unique_candidate_job
        UNIQUE (candidate_id, job_id)
);

CREATE INDEX IF NOT EXISTS applications_job_id_idx ON applications (job_id);
CREATE INDEX IF NOT EXISTS applications_cv_id_idx ON applications (cv_id);
CREATE INDEX IF NOT EXISTS applications_candidate_id_idx ON applications (candidate_id);
CREATE INDEX IF NOT EXISTS applications_recruiter_id_idx ON applications (recruiter_id);
CREATE INDEX IF NOT EXISTS applications_status_idx ON applications (status);
CREATE INDEX IF NOT EXISTS applications_created_at_idx ON applications (created_at);

CREATE OR REPLACE FUNCTION set_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS applications_set_updated_at ON applications;
CREATE TRIGGER applications_set_updated_at
BEFORE UPDATE ON applications
FOR EACH ROW
EXECUTE FUNCTION set_applications_updated_at();
