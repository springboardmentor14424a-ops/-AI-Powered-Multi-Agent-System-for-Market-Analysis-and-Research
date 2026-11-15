from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, preferences, research, stocks, watchlist


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates tables on first run
    yield


app = FastAPI(title="Multi-Agent Stock Research Analyst - Module 1", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
)

for r in (auth.router, preferences.router, stocks.router, watchlist.router, research.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
