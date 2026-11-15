from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.research import router as research_router
from routers.google_auth import router as google_auth_router
from routers.stocks import router as stocks_router
from routers.watchlist import router as watchlist_router
from routers.preferences import router as preferences_router

app = FastAPI(
    title="Multi-Agent Stock Research Analyst",
    description="Backend API for the Multi-Agent Stock Research Analyst platform.",
    version="1.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(research_router)
app.include_router(google_auth_router)
app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(preferences_router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}
