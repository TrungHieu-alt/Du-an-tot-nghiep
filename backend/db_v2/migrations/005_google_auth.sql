-- Additive Google OAuth support for the normal FastAPI/PostgreSQL auth surface.
-- Existing local users remain valid; Google accounts are stored in the same users table.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_id TEXT,
    ADD COLUMN IF NOT EXISTS avatar_url TEXT,
    ADD COLUMN IF NOT EXISTS auth_provider TEXT NOT NULL DEFAULT 'local';

ALTER TABLE users
    ALTER COLUMN role SET DEFAULT 'user';

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_role_chk;

ALTER TABLE users
    ADD CONSTRAINT users_role_chk
        CHECK (role IN ('user', 'candidate', 'employer', 'admin'));

CREATE UNIQUE INDEX IF NOT EXISTS users_google_id_unique_idx
    ON users (google_id)
    WHERE google_id IS NOT NULL;
