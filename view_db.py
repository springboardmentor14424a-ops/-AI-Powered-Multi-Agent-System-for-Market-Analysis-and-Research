"""
Database Inspector Utility
Automatically detects your active database (PostgreSQL or SQLite from backend/.env)
and displays all tables and records in a clean table format.
Usage: python view_db.py
"""

import sys
import os
import subprocess
from pathlib import Path

# Auto-use virtual environment python if available
try:
    from sqlalchemy import create_engine, inspect, text
except ImportError:
    venv_py = Path(__file__).resolve().parent / "backend" / "venv" / "Scripts" / "python.exe"
    if venv_py.exists() and sys.executable.lower() != str(venv_py).lower():
        sys.exit(subprocess.call([str(venv_py), __file__] + sys.argv[1:]))
    raise

# Load DATABASE_URL from backend/.env
ENV_FILE = Path(__file__).resolve().parent / "backend" / ".env"
database_url = "sqlite:///./backend/stock_research.db"

if ENV_FILE.exists():
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                database_url = line.split("=", 1)[1].strip()
                break

print("=" * 65)
print(f"DATABASE INSPECTOR")
print(f"Active URL: {database_url}")
print("=" * 65)

try:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    print(f"\nTables Found ({len(table_names)}): {', '.join(table_names)}")

    with engine.connect() as conn:
        for table in table_names:
            columns = [c["name"] for c in inspector.get_columns(table)]
            query = text(f"SELECT * FROM {table};")
            rows = conn.execute(query).fetchall()

            print(f"\n=======================================================")
            print(f" TABLE: {table.upper()} ({len(rows)} records)")
            print(f"=======================================================")
            if not rows:
                print("  (No records found)")
                continue

            # Header
            print(" | ".join(columns))
            print("-" * 65)
            for row in rows:
                formatted = [
                    str(val)[:28] + "..." if len(str(val)) > 30 else str(val)
                    for val in row
                ]
                print(" | ".join(formatted))

    print("\n" + "=" * 65)
    print("Inspection complete.")
    print("=" * 65)

except Exception as e:
    print(f"\nError inspecting database: {e}")
