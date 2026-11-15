import sqlite3
import os

db_path = r'backend\stock_research.db' if os.path.exists(r'backend\stock_research.db') else 'stock_research.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('SELECT user_id, full_name, email, password_hash, created_at FROM users')
rows = cur.fetchall()

print("=" * 115)
print("                                 REGISTERED USERS DATABASE RECORDS")
print("=" * 115)
print(f"Database File: {os.path.abspath(db_path)}")
print(f"Total Registered Users: {len(rows)}\n")

header = f"{'ID':<4} | {'Full Name':<18} | {'Email Address':<28} | {'Bcrypt Password Hash (Never Plaintext)'}"
print(header)
print("-" * 115)

for r in rows:
    print(f"{r[0]:<4} | {r[1]:<18} | {r[2]:<28} | {r[3]}")

print("=" * 115)
conn.close()

