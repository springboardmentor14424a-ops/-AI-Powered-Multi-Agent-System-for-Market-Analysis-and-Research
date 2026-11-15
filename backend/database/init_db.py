"""
init_db.py
----------
Reads DATABASE_URL from the environment and executes schema.sql against
the target PostgreSQL database using psycopg2.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname python init_db.py
"""

import os
import pathlib
import sys

import psycopg2
from dotenv import load_dotenv

# Load .env from the backend root (one level up from this file)
_env_path = pathlib.Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)


def init_db() -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # psycopg2 uses postgresql://, not postgresql+asyncpg://
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    schema_path = pathlib.Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"ERROR: schema.sql not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    sql = schema_path.read_text(encoding="utf-8")

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.close()
        print("Database schema initialised successfully.")
    except psycopg2.Error as exc:
        print(f"ERROR: Failed to initialise database schema: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    init_db()
