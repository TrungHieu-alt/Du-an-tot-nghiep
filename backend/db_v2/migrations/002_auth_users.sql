-- JobConnect authentication users.
-- Additive surface for /api/auth/*; Matching V2 prototype tables remain unchanged.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    role          TEXT NOT NULL DEFAULT 'candidate',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_email_nonempty_chk
        CHECK (length(trim(email)) > 0),
    CONSTRAINT users_password_hash_nonempty_chk
        CHECK (length(trim(password_hash)) > 0),
    CONSTRAINT users_role_chk
        CHECK (role IN ('candidate', 'employer', 'admin'))
);

CREATE UNIQUE INDEX users_email_lower_unique_idx ON users (lower(email));

CREATE OR REPLACE FUNCTION set_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_users_updated_at();
