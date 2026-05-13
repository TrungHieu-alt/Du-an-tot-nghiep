-- Backfill public defaults for existing normal Job/CV deployments.
-- This migration touches only normal tables; V2 prototype tables are unchanged.

ALTER TABLE jobs ALTER COLUMN status SET DEFAULT 'published';
ALTER TABLE jobs ALTER COLUMN visibility SET DEFAULT 'public';
ALTER TABLE jobs ALTER COLUMN archived SET DEFAULT false;

UPDATE jobs
SET status = 'published',
    visibility = 'public',
    archived = false
WHERE archived = false;

ALTER TABLE cvs ALTER COLUMN status SET DEFAULT 'published';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS visibility TEXT NOT NULL DEFAULT 'public';
ALTER TABLE cvs ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE cvs ALTER COLUMN visibility SET DEFAULT 'public';
ALTER TABLE cvs ALTER COLUMN archived SET DEFAULT false;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'cvs_visibility_chk'
    ) THEN
        ALTER TABLE cvs
        ADD CONSTRAINT cvs_visibility_chk
        CHECK (visibility IN ('public', 'private', 'unlisted'));
    END IF;
END $$;

UPDATE cvs
SET status = 'published',
    visibility = 'public',
    archived = false
WHERE status IS NULL
   OR status IN ('draft', 'published')
   OR visibility IS NULL
   OR archived IS NULL;

CREATE INDEX IF NOT EXISTS cvs_visibility_idx ON cvs (visibility);
CREATE INDEX IF NOT EXISTS cvs_archived_idx ON cvs (archived);
