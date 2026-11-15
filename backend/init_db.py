import sys
import logging
from app.database import engine, Base
from app.models import User, SavedStock, ResearchTask, UserPreference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db")

def init_database():
    logger.info(f"Target Database Engine URL: {engine.url}")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created/verified tables:")
        logger.info("- users (user_id PK, full_name, email UNIQUE, password_hash, created_at)")
        logger.info("- saved_stocks (saved_stock_id PK, user_id FK, ticker, created_at, UNIQUE(user_id, ticker))")
        logger.info("- research_tasks (task_id PK, user_id FK, ticker, market, requested_period, status, created_at, completed_at)")
        logger.info("- user_preferences (preference_id PK, user_id FK UNIQUE, preferred_market, preferred_analysis_period, updated_at)")
        print("\nDatabase Schema Initialization Complete!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()

