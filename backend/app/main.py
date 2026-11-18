import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, watchlist, history, preferences, stocks, market_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock_research.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        # Ensure backward compatibility for company_name column if using SQLite
        with engine.connect() as conn:
            from sqlalchemy import text
            try:
                conn.execute(text("SELECT company_name FROM research_tasks LIMIT 1"))
            except Exception:
                try:
                    conn.execute(text("ALTER TABLE research_tasks ADD COLUMN company_name VARCHAR(120)"))
                    conn.commit()
                except Exception:
                    pass
        logger.info("Database tables and columns verified successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Multi-Agent Stock Research Analyst Platform (Module 1: Auth & Workspace, Module 2: Stock Search & Market Data Collection)",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration to allow seamless frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev & testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(watchlist.router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(preferences.router, prefix=settings.API_V1_STR)
app.include_router(stocks.router, prefix=settings.API_V1_STR)
app.include_router(market_data.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "modules": [
            "Module 1: User Authentication & Research Workspace",
            "Module 2: Stock Search & Market Data Collection"
        ],
        "docs_url": "/docs",
        "version": "2.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "database": str(engine.url)}

