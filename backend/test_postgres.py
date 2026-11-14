"""
PostgreSQL Connection Tester
Usage: python test_postgres.py
"""

import sys
from sqlalchemy import create_engine, text
from app.config import settings

def test_connection():
    print(f"Testing database connection using URL from configuration:")
    # Mask password for display
    url = settings.DATABASE_URL
    print(f"Target: {url}")

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).fetchone()
            print("\nSUCCESS! Successfully connected to database server.")
            print(f"Version: {result[0]}")
            
            # List existing tables
            tables_query = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)).fetchall()
            table_names = [t[0] for t in tables_query]
            print(f"Tables in database ({len(table_names)}): {', '.join(table_names) if table_names else 'None (will be auto-created on backend startup)'}")
            return True
    except Exception as e:
        print("\nCONNECTION FAILED:")
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Is PostgreSQL service started? Run 'net start postgresql-x64-18' in Admin CMD.")
        print("2. Is the password in backend/.env correct?")
        print("3. Is the database created in pgAdmin / psql?")
        return False

if __name__ == "__main__":
    test_connection()
