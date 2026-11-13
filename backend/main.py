from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import marketdata
import models
import schemas
from database import Base, engine, get_db
from security import create_token, get_current_user, hash_password, verify_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates the tables if they don't exist
    yield


app = FastAPI(title="Multi-Agent Stock Research Analyst", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- Registration and login ----------
@app.post("/api/auth/register", status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(models.User).where(models.User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already registered.")
    user = models.User(
        full_name=body.full_name,
        email=email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already registered.")
    return {"message": "Registration successful. Please sign in."}


@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    return schemas.TokenOut(access_token=create_token(user.user_id))


# ---------- Protected endpoints (a valid token is required) ----------
@app.get("/api/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.put("/api/me/preferences", response_model=schemas.UserOut)
def save_preferences(
    body: schemas.PreferencesIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.preferred_market = body.preferred_market
    user.default_period = body.default_period
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/watchlist", response_model=list[schemas.SavedStockOut])
def get_watchlist(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(models.SavedStock).where(models.SavedStock.user_id == user.user_id)
    return db.scalars(q.order_by(models.SavedStock.created_at.desc())).all()


@app.post("/api/watchlist", response_model=schemas.SavedStockOut, status_code=201)
def add_to_watchlist(
    body: schemas.StockIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exists = db.scalar(
        select(models.SavedStock).where(
            models.SavedStock.user_id == user.user_id, models.SavedStock.ticker == body.ticker
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{body.ticker} is already in your watchlist.")
    item = models.SavedStock(user_id=user.user_id, ticker=body.ticker)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/watchlist/{saved_stock_id}", status_code=204)
def remove_from_watchlist(
    saved_stock_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(models.SavedStock, saved_stock_id)
    # Only the owner may delete: the owner comes from the token, not from the browser.
    if item is None or item.user_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stock not found.")
    db.delete(item)
    db.commit()


@app.post("/api/research-tasks", response_model=schemas.ResearchTaskOut, status_code=201)
def start_research(
    body: schemas.TaskIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a research task for the logged-in user (the agents that run it come later)."""
    task = models.ResearchTask(
        user_id=user.user_id,  # taken from the verified token, never from the browser
        ticker=marketdata.normalize_ticker(body.ticker, body.market),
        market=body.market,
        requested_period=body.period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/research-history", response_model=list[schemas.ResearchTaskOut])
def research_history(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(models.ResearchTask).where(models.ResearchTask.user_id == user.user_id)
    return db.scalars(q.order_by(models.ResearchTask.created_at.desc())).all()


# ---------- Point 2: stock search and market data (Yahoo Finance) ----------
@app.get("/api/stocks/search")
def stock_search(
    q: str = Query(min_length=2, max_length=60),
    market: schemas.Market | None = None,
    user: models.User = Depends(get_current_user),
):
    try:
        return marketdata.search_stocks(q, market)
    except marketdata.MarketDataError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@app.get("/api/stocks/{ticker}/history")
def stock_history(
    ticker: str,
    period: schemas.Period = "1Y",
    market: schemas.Market | None = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    symbol = marketdata.normalize_ticker(ticker, market or "")
    try:
        data = marketdata.get_history(symbol, period)
    except marketdata.MarketDataError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))

    if not data["from_cache"]:
        # Record where the data came from and when it was retrieved.
        db.add(models.SourceDocument(
            source_type="market_data",
            title=f"Price history (OHLCV): {symbol}, {period}",
            source_url=data["source"]["url"],
            content_hash=marketdata.content_hash(data),
        ))
        db.commit()
    return data


@app.get("/api/stocks/{ticker}/profile")
def stock_profile(
    ticker: str,
    market: schemas.Market | None = None,
    user: models.User = Depends(get_current_user),
):
    symbol = marketdata.normalize_ticker(ticker, market or "")
    try:
        return marketdata.get_profile(symbol)
    except marketdata.MarketDataError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
