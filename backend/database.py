
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ---------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:password@localhost:5432/stock_analyst"
)

# ---------------------------------------------------------
# DATABASE ENGINE
# ---------------------------------------------------------

engine_options = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }
else:
    engine_options.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_engine(
    DATABASE_URL,
    **engine_options
)


# ---------------------------------------------------------
# SESSION CONFIGURATION
# ---------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# ---------------------------------------------------------
# BASE MODEL
# ---------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------
# DATABASE SESSION DEPENDENCY
# ---------------------------------------------------------

def get_db():
    """Provide a database session for each API request."""

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
