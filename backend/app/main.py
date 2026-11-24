
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import settings
from app.routes import (
    auth,
    dashboard,
    research,
    watchlist,
    stock_search,
    preferences,
    stock_data
)


# Initialize FastAPI
app = FastAPI(
    title="StockPilot API",
    description="User Authentication and Research Workspace",
    version="1.0.0"
)


# CORS configuration
allowed_origins = list({
    settings.FRONTEND_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173"
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Content-Type",
        "X-CSRF-Token"
    ]
)


# Register API routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(research.router)
app.include_router(watchlist.router)
app.include_router(stock_search.router)
app.include_router(preferences.router)
app.include_router(stock_data.router)


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "StockPilot API is running"
    }


# Health endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
