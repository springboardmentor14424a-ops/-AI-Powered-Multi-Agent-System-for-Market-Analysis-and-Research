import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("stock_research.database")
logging.basicConfig(level=logging.INFO)

DATABASE_URL = settings.DATABASE_URL
engine = None

if DATABASE_URL.startswith("postgresql"):
    try:
        temp_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 1}
        )
        with temp_engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL database!")
        engine = temp_engine
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection to {DATABASE_URL} failed ({e}). "
            "Using SQLite database 'sqlite:///./stock_research.db' for continuous availability."
        )
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sqlite_file = os.path.join(backend_dir, "stock_research.db").replace("\\", "/")
        engine = create_engine(f"sqlite:///{sqlite_file}", connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
