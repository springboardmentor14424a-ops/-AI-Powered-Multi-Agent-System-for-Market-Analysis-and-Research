from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, stocks

app = FastAPI(title="StockMind AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stocks.router)


@app.get("/")
def root():
    return {"message": "StockMind AI API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
