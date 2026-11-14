
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, research, stocks, watchlist, preferences

app = FastAPI(
    title="Multi-Agent Stock Research Analyst API",
    description="User authentication, research workspace and stock market data",
    version="1.0.0"
)

# Allow the React development server to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Research routes
app.include_router(
    research.router,
    prefix="/research",
    tags=["Research"]
)

# Stock data routes
app.include_router(
    stocks.router
)

# Watchlist routes
app.include_router(
    watchlist.router,
    prefix="/watchlist",
    tags=["Watchlist"]
)

# User preferences routes
app.include_router(
    preferences.router,
    prefix="/preferences",
    tags=["Preferences"]
)


@app.get("/")
def root():
    return {"message": "Stock Research Analyst API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
