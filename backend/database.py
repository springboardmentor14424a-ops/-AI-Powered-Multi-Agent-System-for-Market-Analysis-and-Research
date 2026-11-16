
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env
load_dotenv()

# Read the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine
engine = create_engine(DATABASE_URL, echo=True)

# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()
# Get database session for each API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()