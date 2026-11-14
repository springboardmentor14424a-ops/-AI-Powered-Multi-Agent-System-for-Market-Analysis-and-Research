
from app.database import engine

try:
    with engine.connect() as connection:
        print("PostgreSQL connected successfully!")
        print("Database:", connection.engine.url.database)

except Exception as e:
    print("Database connection failed!")
    print(e)
