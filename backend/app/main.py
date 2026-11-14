from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import settings
from app.models import User, UserPreference, SavedStock, ResearchTask, ResearchReport, UserSession
from app.routers import auth, preferences, watchlist, tasks

# Auto-create all database tables on application startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Agent Stock Research Analyst API",
    description="Module 1: User Authentication and Research Workspace",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(preferences.router)
app.include_router(watchlist.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {
        "project": "Multi-Agent Stock Research Analyst",
        "module": "Module 1: User Authentication and Research Workspace",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
