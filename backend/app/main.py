
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.database import engine
from app.routes.auth import router as auth_router
from app.routes.stock import router as stock_router
from app.routes.watchlist import router as watchlist_router
from app.routes.preference import router as preference_router
from app.routes.research import router as research_router


app = FastAPI(
    title="Multi-Agent Stock Research Analyst",
    description="AI-powered stock market research platform",
    version="1.0.0",
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Stock Research API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/db-check")
def database_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        return {
            "database_status": "connected",
            "test_result": value,
        }

    except SQLAlchemyError:
        return {
            "database_status": "failed",
        }


# Register API routes
app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(watchlist_router)
app.include_router(preference_router)
app.include_router(research_router)
