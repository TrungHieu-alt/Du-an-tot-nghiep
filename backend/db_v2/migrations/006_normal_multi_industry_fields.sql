-- Multi-industry enum-normalized fields for normal Job/CV storage.
-- This migration touches only normal tables. V2 prototype tables remain unchanged.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS industry TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS occupation_group TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS must_have_skills JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS nice_to_have_skills JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tools_and_technologies TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS domain_knowledge TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS required_education JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS required_certifications TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS embedding JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE jobs ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE jobs ALTER COLUMN visibility SET DEFAULT 'private';

UPDATE jobs
SET industry = 'unknown'
WHERE industry IS NULL OR trim(industry) = '';

UPDATE jobs
SET industry = CASE
        WHEN company_industry ILIKE '%Information Technology%' OR company_industry ILIKE '%Software%' THEN 'information_technology'
        WHEN company_industry ILIKE '%Accounting%' OR company_industry ILIKE '%Finance%' THEN 'accounting_finance'
        WHEN company_industry ILIKE '%Sales%' THEN 'sales'
        WHEN company_industry ILIKE '%Marketing%' THEN 'marketing'
        WHEN company_industry ILIKE '%Human Resources%' OR company_industry ILIKE '%HR%' THEN 'human_resources'
        WHEN company_industry ILIKE '%Education%' THEN 'education'
        WHEN company_industry ILIKE '%Healthcare%' THEN 'healthcare'
        WHEN company_industry ILIKE '%Construction%' OR company_industry ILIKE '%Engineering%' THEN 'engineering_construction'
        WHEN company_industry ILIKE '%Design%' OR company_industry ILIKE '%Creative%' THEN 'design_creative'
        WHEN company_industry ILIKE '%Customer Service%' THEN 'customer_service'
        WHEN company_industry ILIKE '%Operations%' THEN 'operations'
        WHEN company_industry ILIKE '%Logistics%' OR company_industry ILIKE '%Supply Chain%' THEN 'logistics_supply_chain'
        WHEN company_industry ILIKE '%Hospitality%' OR company_industry ILIKE '%Tourism%' THEN 'hospitality_tourism'
        WHEN company_industry ILIKE '%Legal%' THEN 'legal'
        WHEN company_industry ILIKE '%Manufacturing%' THEN 'manufacturing'
        WHEN company_industry ILIKE '%Retail%' THEN 'retail'
        ELSE industry
    END
WHERE industry = 'unknown';

UPDATE jobs
SET occupation_group = 'unknown'
WHERE occupation_group IS NULL OR trim(occupation_group) = '';

UPDATE jobs
SET occupation_group = CASE
        WHEN title ILIKE '%DevOps%' THEN 'devops_cloud'
        WHEN title ILIKE '%Backend%' OR title ILIKE '%Frontend%' OR title ILIKE '%Developer%' OR title ILIKE '%Engineer%' THEN 'software_engineering'
        WHEN title ILIKE '%Marketing%' THEN 'digital_marketing'
        WHEN title ILIKE '%Sales%' THEN 'sales_executive'
        WHEN title ILIKE '%Accountant%' OR title ILIKE '%Accounting%' THEN 'accountant'
        WHEN title ILIKE '%Finance%' THEN 'financial_analyst'
        WHEN title ILIKE '%HR%' OR title ILIKE '%Recruit%' THEN 'hr_recruitment'
        WHEN title ILIKE '%Teacher%' THEN 'teacher'
        WHEN title ILIKE '%Doctor%' THEN 'doctor'
        WHEN title ILIKE '%Nurse%' THEN 'nurse'
        WHEN title ILIKE '%Designer%' THEN 'ui_ux_designer'
        WHEN title ILIKE '%Customer%' THEN 'customer_support'
        WHEN title ILIKE '%Logistics%' THEN 'logistics_staff'
        WHEN title ILIKE '%Legal%' THEN 'legal_staff'
        WHEN title ILIKE '%Production%' THEN 'production_worker'
        WHEN title ILIKE '%Retail%' THEN 'retail_staff'
        WHEN title ILIKE '%Hotel%' THEN 'hotel_staff'
        ELSE occupation_group
    END
WHERE occupation_group = 'unknown';

ALTER TABLE jobs ALTER COLUMN industry SET DEFAULT 'unknown';
ALTER TABLE jobs ALTER COLUMN industry SET NOT NULL;
ALTER TABLE jobs ALTER COLUMN occupation_group SET DEFAULT 'unknown';
ALTER TABLE jobs ALTER COLUMN occupation_group SET NOT NULL;

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_status_chk;
ALTER TABLE jobs
    ADD CONSTRAINT jobs_status_chk
    CHECK (status IN ('draft', 'published', 'closed', 'unknown'));

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_visibility_chk;
ALTER TABLE jobs
    ADD CONSTRAINT jobs_visibility_chk
    CHECK (visibility IN ('public', 'private', 'unlisted', 'unknown'));

CREATE INDEX IF NOT EXISTS jobs_industry_idx ON jobs (industry);
CREATE INDEX IF NOT EXISTS jobs_occupation_group_idx ON jobs (occupation_group);
CREATE INDEX IF NOT EXISTS jobs_seniority_idx ON jobs (seniority);
CREATE INDEX IF NOT EXISTS jobs_education_level_idx ON jobs (education_level);
CREATE INDEX IF NOT EXISTS jobs_must_have_skills_gin_idx ON jobs USING GIN (must_have_skills);
CREATE INDEX IF NOT EXISTS jobs_nice_to_have_skills_gin_idx ON jobs USING GIN (nice_to_have_skills);
CREATE INDEX IF NOT EXISTS jobs_tools_and_technologies_gin_idx ON jobs USING GIN (tools_and_technologies);
CREATE INDEX IF NOT EXISTS jobs_domain_knowledge_gin_idx ON jobs USING GIN (domain_knowledge);
CREATE INDEX IF NOT EXISTS jobs_required_education_gin_idx ON jobs USING GIN (required_education);
CREATE INDEX IF NOT EXISTS jobs_required_certifications_gin_idx ON jobs USING GIN (required_certifications);
CREATE INDEX IF NOT EXISTS jobs_embedding_gin_idx ON jobs USING GIN (embedding);

ALTER TABLE cvs ADD COLUMN IF NOT EXISTS industry TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS occupation_group TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS career_level TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS years_of_experience NUMERIC NOT NULL DEFAULT 0;
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS tools_and_technologies TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS domain_knowledge TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS embedding JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE cvs ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE cvs ALTER COLUMN visibility SET DEFAULT 'private';

UPDATE cvs
SET industry = 'unknown'
WHERE industry IS NULL OR trim(industry) = '';

UPDATE cvs
SET industry = CASE
        WHEN target_role ILIKE '%Developer%' OR target_role ILIKE '%Backend%' OR target_role ILIKE '%Frontend%' OR summary ILIKE '%React%' OR summary ILIKE '%Python%' THEN 'information_technology'
        WHEN target_role ILIKE '%Account%' OR summary ILIKE '%Finance%' THEN 'accounting_finance'
        WHEN target_role ILIKE '%Sales%' THEN 'sales'
        WHEN target_role ILIKE '%Marketing%' THEN 'marketing'
        WHEN target_role ILIKE '%HR%' OR target_role ILIKE '%Recruit%' THEN 'human_resources'
        WHEN target_role ILIKE '%Teacher%' THEN 'education'
        WHEN target_role ILIKE '%Doctor%' OR target_role ILIKE '%Nurse%' THEN 'healthcare'
        WHEN target_role ILIKE '%Designer%' OR summary ILIKE '%Figma%' THEN 'design_creative'
        WHEN target_role ILIKE '%Logistics%' THEN 'logistics_supply_chain'
        WHEN target_role ILIKE '%Customer%' THEN 'customer_service'
        WHEN target_role ILIKE '%Hotel%' OR target_role ILIKE '%Receptionist%' THEN 'hospitality_tourism'
        ELSE industry
    END
WHERE industry = 'unknown';

UPDATE cvs
SET occupation_group = 'unknown'
WHERE occupation_group IS NULL OR trim(occupation_group) = '';

UPDATE cvs
SET occupation_group = CASE
        WHEN target_role ILIKE '%Backend%' OR target_role ILIKE '%Frontend%' OR target_role ILIKE '%Developer%' THEN 'software_engineering'
        WHEN target_role ILIKE '%Account%' THEN 'accountant'
        WHEN target_role ILIKE '%Sales%' THEN 'sales_executive'
        WHEN target_role ILIKE '%Marketing%' THEN 'digital_marketing'
        WHEN target_role ILIKE '%HR%' OR target_role ILIKE '%Recruit%' THEN 'hr_recruitment'
        WHEN target_role ILIKE '%Teacher%' THEN 'teacher'
        WHEN target_role ILIKE '%Designer%' THEN 'ui_ux_designer'
        WHEN target_role ILIKE '%Customer%' THEN 'customer_support'
        WHEN target_role ILIKE '%Hotel%' OR target_role ILIKE '%Receptionist%' THEN 'hotel_staff'
        ELSE occupation_group
    END
WHERE occupation_group = 'unknown';

UPDATE cvs
SET career_level = 'unknown'
WHERE career_level IS NULL OR trim(career_level) = '';

ALTER TABLE cvs ALTER COLUMN industry SET DEFAULT 'unknown';
ALTER TABLE cvs ALTER COLUMN industry SET NOT NULL;
ALTER TABLE cvs ALTER COLUMN occupation_group SET DEFAULT 'unknown';
ALTER TABLE cvs ALTER COLUMN occupation_group SET NOT NULL;
ALTER TABLE cvs ALTER COLUMN career_level SET DEFAULT 'unknown';
ALTER TABLE cvs ALTER COLUMN career_level SET NOT NULL;
ALTER TABLE cvs ALTER COLUMN years_of_experience SET DEFAULT 0;
ALTER TABLE cvs ALTER COLUMN years_of_experience SET NOT NULL;

ALTER TABLE cvs DROP CONSTRAINT IF EXISTS cvs_status_chk;
ALTER TABLE cvs
    ADD CONSTRAINT cvs_status_chk
    CHECK (status IN ('draft', 'published', 'archived', 'unknown'));

ALTER TABLE cvs DROP CONSTRAINT IF EXISTS cvs_visibility_chk;
ALTER TABLE cvs
    ADD CONSTRAINT cvs_visibility_chk
    CHECK (visibility IN ('public', 'private', 'unlisted', 'unknown'));

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'cvs_years_of_experience_nonnegative_chk'
    ) THEN
        ALTER TABLE cvs
        ADD CONSTRAINT cvs_years_of_experience_nonnegative_chk
        CHECK (years_of_experience >= 0);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS cvs_industry_idx ON cvs (industry);
CREATE INDEX IF NOT EXISTS cvs_occupation_group_idx ON cvs (occupation_group);
CREATE INDEX IF NOT EXISTS cvs_career_level_idx ON cvs (career_level);
CREATE INDEX IF NOT EXISTS cvs_years_of_experience_idx ON cvs (years_of_experience);
CREATE INDEX IF NOT EXISTS cvs_tools_and_technologies_gin_idx ON cvs USING GIN (tools_and_technologies);
CREATE INDEX IF NOT EXISTS cvs_domain_knowledge_gin_idx ON cvs USING GIN (domain_knowledge);
CREATE INDEX IF NOT EXISTS cvs_embedding_gin_idx ON cvs USING GIN (embedding);
