
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import User, Watchlist
from app.auth import router
from app.finance import router as finance_router
from app.watchlist import router as watchlist_router

app = FastAPI(
    title="Multi-Agent Stock Analyst API"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)
app.include_router(finance_router)
app.include_router(watchlist_router)


@app.get("/")
def home():
    return {
        "message": "Stock Analyst API is running"
    }
