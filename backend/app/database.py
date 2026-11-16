from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 1. Create the SQLAlchemy engine (connection bridge to PostgreSQL)
engine = create_engine(settings.DATABASE_URL)

# 2. Create a Session factory (each API request gets its own isolated session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base class that all our database table models will inherit from
Base = declarative_base()

# 4. Dependency function to safely open and close a DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()