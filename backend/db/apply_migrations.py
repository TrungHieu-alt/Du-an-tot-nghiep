from __future__ import annotations

from pathlib import Path

from jobconnect.core.database import get_connection


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def main() -> None:
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        raise SystemExit("no migrations found")

    with get_connection() as conn, conn.cursor() as cur:
        for sql_file in sql_files:
            cur.execute(sql_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
