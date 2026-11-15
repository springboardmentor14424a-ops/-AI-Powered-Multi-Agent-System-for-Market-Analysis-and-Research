import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname='stock_research'")
if not cur.fetchone():
    cur.execute("CREATE DATABASE stock_research")
    print("✅ Database 'stock_research' created successfully!")
else:
    print("ℹ️  Database 'stock_research' already exists.")
conn.close()

