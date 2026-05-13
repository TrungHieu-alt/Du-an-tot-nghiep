-- JobConnect normal Job/CV storage.
-- Additive surface for normal search and owner-managed Job/CV CRUD.
-- Matching V2 prototype tables remain unchanged.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS jobs (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id             TEXT,
    title                  TEXT NOT NULL,
    slug                   TEXT,
    status                 TEXT NOT NULL DEFAULT 'published',
    visibility             TEXT NOT NULL DEFAULT 'public',
    company_name           TEXT,
    company_logo_url       TEXT,
    company_website        TEXT,
    company_location       TEXT,
    company_size           TEXT,
    company_industry       TEXT,
    department             TEXT,
    location               JSONB NOT NULL DEFAULT '{}'::jsonb,
    employment_type        TEXT[] NOT NULL DEFAULT '{}',
    seniority              TEXT,
    team_size              INTEGER,
    description            TEXT,
    responsibilities       TEXT[] NOT NULL DEFAULT '{}',
    requirements           TEXT[] NOT NULL DEFAULT '{}',
    nice_to_have           TEXT[] NOT NULL DEFAULT '{}',
    skills                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    experience_years       NUMERIC,
    education_level        TEXT,
    salary                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    benefits               TEXT[] NOT NULL DEFAULT '{}',
    bonus                  TEXT,
    equity                 TEXT,
    apply_url              TEXT,
    apply_email            TEXT,
    recruiter              JSONB NOT NULL DEFAULT '{}'::jsonb,
    how_to_apply           TEXT,
    application_deadline   TIMESTAMPTZ,
    tags                   TEXT[] NOT NULL DEFAULT '{}',
    categories             TEXT[] NOT NULL DEFAULT '{}',
    remote                 BOOLEAN NOT NULL DEFAULT FALSE,
    views                  INTEGER NOT NULL DEFAULT 0,
    applications_count     INTEGER NOT NULL DEFAULT 0,
    pre_screen_questions   JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_docs          TEXT[] NOT NULL DEFAULT '{}',
    published_by           TEXT,
    approved_at            TIMESTAMPTZ,
    approved_by            TEXT,
    archived               BOOLEAN NOT NULL DEFAULT FALSE,
    version                INTEGER NOT NULL DEFAULT 1,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jobs_title_nonempty_chk
        CHECK (length(trim(title)) > 0),
    CONSTRAINT jobs_status_chk
        CHECK (status IN ('draft', 'published', 'closed')),
    CONSTRAINT jobs_visibility_chk
        CHECK (visibility IN ('public', 'private', 'unlisted')),
    CONSTRAINT jobs_views_nonnegative_chk
        CHECK (views >= 0),
    CONSTRAINT jobs_applications_count_nonnegative_chk
        CHECK (applications_count >= 0),
    CONSTRAINT jobs_version_positive_chk
        CHECK (version >= 1)
);

CREATE TABLE IF NOT EXISTS cvs (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    avatar_url         TEXT,
    fullname           TEXT NOT NULL DEFAULT '',
    preferred_name     TEXT,
    email              TEXT,
    phone              TEXT,
    location           JSONB NOT NULL DEFAULT '{}'::jsonb,
    headline           TEXT,
    summary            TEXT,
    target_role        TEXT,
    employment_type    TEXT[] NOT NULL DEFAULT '{}',
    salary_expectation TEXT,
    availability       TEXT,
    skills             JSONB NOT NULL DEFAULT '[]'::jsonb,
    experiences        JSONB NOT NULL DEFAULT '[]'::jsonb,
    education          JSONB NOT NULL DEFAULT '[]'::jsonb,
    projects           JSONB NOT NULL DEFAULT '[]'::jsonb,
    certifications     JSONB NOT NULL DEFAULT '[]'::jsonb,
    languages          JSONB NOT NULL DEFAULT '[]'::jsonb,
    portfolio          JSONB NOT NULL DEFAULT '[]'::jsonb,
    "references"       JSONB NOT NULL DEFAULT '[]'::jsonb,
    status             TEXT NOT NULL DEFAULT 'published',
    visibility         TEXT NOT NULL DEFAULT 'public',
    tags               TEXT[] NOT NULL DEFAULT '{}',
    version            INTEGER NOT NULL DEFAULT 1,
    file               JSONB NOT NULL DEFAULT '{}'::jsonb,
    archived           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cvs_status_nonempty_chk
        CHECK (length(trim(status)) > 0),
    CONSTRAINT cvs_visibility_chk
        CHECK (visibility IN ('public', 'private', 'unlisted')),
    CONSTRAINT cvs_version_positive_chk
        CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS jobs_created_by_idx ON jobs (created_by);
CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs (status);
CREATE INDEX IF NOT EXISTS jobs_visibility_idx ON jobs (visibility);
CREATE INDEX IF NOT EXISTS jobs_archived_idx ON jobs (archived);
CREATE INDEX IF NOT EXISTS jobs_title_lower_idx ON jobs (lower(title));
CREATE INDEX IF NOT EXISTS jobs_company_name_lower_idx ON jobs (lower(company_name));
CREATE INDEX IF NOT EXISTS jobs_company_industry_lower_idx ON jobs (lower(company_industry));
CREATE INDEX IF NOT EXISTS jobs_department_lower_idx ON jobs (lower(department));
CREATE INDEX IF NOT EXISTS jobs_remote_idx ON jobs (remote);
CREATE INDEX IF NOT EXISTS jobs_categories_gin_idx ON jobs USING GIN (categories);
CREATE INDEX IF NOT EXISTS jobs_tags_gin_idx ON jobs USING GIN (tags);
CREATE INDEX IF NOT EXISTS jobs_employment_type_gin_idx ON jobs USING GIN (employment_type);
CREATE INDEX IF NOT EXISTS jobs_skills_gin_idx ON jobs USING GIN (skills);
CREATE INDEX IF NOT EXISTS jobs_location_gin_idx ON jobs USING GIN (location);
CREATE INDEX IF NOT EXISTS jobs_salary_gin_idx ON jobs USING GIN (salary);

CREATE INDEX IF NOT EXISTS cvs_created_by_idx ON cvs (created_by);
CREATE INDEX IF NOT EXISTS cvs_fullname_lower_idx ON cvs (lower(fullname));
CREATE INDEX IF NOT EXISTS cvs_target_role_lower_idx ON cvs (lower(target_role));
CREATE INDEX IF NOT EXISTS cvs_status_idx ON cvs (status);
CREATE INDEX IF NOT EXISTS cvs_visibility_idx ON cvs (visibility);
CREATE INDEX IF NOT EXISTS cvs_archived_idx ON cvs (archived);
CREATE INDEX IF NOT EXISTS cvs_tags_gin_idx ON cvs USING GIN (tags);
CREATE INDEX IF NOT EXISTS cvs_skills_gin_idx ON cvs USING GIN (skills);
CREATE INDEX IF NOT EXISTS cvs_location_gin_idx ON cvs USING GIN (location);
CREATE INDEX IF NOT EXISTS cvs_file_gin_idx ON cvs USING GIN (file);

CREATE OR REPLACE FUNCTION set_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS jobs_set_updated_at ON jobs;
CREATE TRIGGER jobs_set_updated_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION set_jobs_updated_at();

CREATE OR REPLACE FUNCTION set_cvs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS cvs_set_updated_at ON cvs;
CREATE TRIGGER cvs_set_updated_at
BEFORE UPDATE ON cvs
FOR EACH ROW
EXECUTE FUNCTION set_cvs_updated_at();
