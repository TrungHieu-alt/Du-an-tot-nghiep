"""Reset, migrate, and seed the Matching V2 prototype PostgreSQL database.

Usage (from the repo root, with the postgres compose service running):

    python backend/db_v2/reset.py

The script drops and recreates the public schema, applies every SQL file under
`migrations/` in lexical order, then applies every SQL file under `seeds/` in
lexical order. Connection details come from environment variables (see
`.env.example`): POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD,
POSTGRES_DB.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg

DB_V2_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = DB_V2_DIR / "migrations"
SEEDS_DIR = DB_V2_DIR / "seeds"
BACKEND_DIR = DB_V2_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _conninfo() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5433')} "
        f"user={os.getenv('POSTGRES_USER', 'jobmatcher')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'jobmatcher')} "
        f"dbname={os.getenv('POSTGRES_DB', 'jobmatcher_v2')}"
    )


def _apply_sql_files(cur: psycopg.Cursor, directory: Path, label: str) -> None:
    if not directory.exists():
        print(f"[{label}] skipped — directory not found: {directory}")
        return
    files = sorted(directory.glob("*.sql"))
    if not files:
        print(f"[{label}] no .sql files in {directory}")
        return
    for path in files:
        print(f"[{label}] applying {path.name}")
        cur.execute(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=("base", "scenario"),
        default=os.getenv("DB_V2_SEED_PROFILE", "base"),
        help="Seed profile after migration. base applies SQL seeds; scenario applies Slice 6B JSON seed.",
    )
    args = parser.parse_args()

    conninfo = _conninfo()
    print(f"[reset] connecting: {conninfo}")
    with psycopg.connect(conninfo, autocommit=False) as conn:
        with conn.cursor() as cur:
            print("[reset] dropping and recreating public schema")
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cur.execute("CREATE SCHEMA public;")
            _apply_sql_files(cur, MIGRATIONS_DIR, "migrate")
            if args.profile == "base":
                _apply_sql_files(cur, SEEDS_DIR, "seed")
            else:
                from db_v2.seed_scenario import seed_scenario

                print("[seed] applying scenario profile matching_v2_slice_6b.json")
                seed_scenario(conn)
        conn.commit()
    print(f"[reset] done profile={args.profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
