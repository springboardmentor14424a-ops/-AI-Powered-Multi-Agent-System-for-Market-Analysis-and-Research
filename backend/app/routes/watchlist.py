
import math

import yfinance as yf

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.auth import get_current_user, validate_csrf
from app.models import User, SavedStock
from app.schemas import SavedStockCreate, SavedStockResponse
from app.constants import SUPPORTED_MARKETS


router = APIRouter(
    prefix="/api/watchlist",
    tags=["Watchlist"]
)


# --------------------------------------------------
# VALIDATE STOCK MARKET
# --------------------------------------------------

def normalize_market(market: str) -> str:

    normalized_market = market.strip().upper()

    if normalized_market not in SUPPORTED_MARKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported market. Supported markets: {', '.join(SUPPORTED_MARKETS)}"
        )

    return normalized_market


# --------------------------------------------------
# CONVERT TICKER TO YFINANCE SYMBOL
# --------------------------------------------------

def get_provider_symbol(ticker: str, market: str) -> str:

    ticker = ticker.strip().upper()

    # Indian NSE symbols
    if market == "NSE":
        if ticker.endswith(".NS"):
            return ticker
        return f"{ticker}.NS"

    # Indian BSE symbols
    if market == "BSE":
        if ticker.endswith(".BO"):
            return ticker
        return f"{ticker}.BO"

    # US markets
    return ticker


# --------------------------------------------------
# FETCH STOCK PRICE
# --------------------------------------------------

def get_stock_price(ticker: str, market: str):

    provider_symbol = get_provider_symbol(ticker, market)

    try:
        stock = yf.Ticker(provider_symbol)
        fast_info = stock.fast_info

        current_price = float(fast_info["last_price"])
        previous_close = float(fast_info["previous_close"])

        if (
            not math.isfinite(current_price)
            or not math.isfinite(previous_close)
            or previous_close == 0
        ):
            return None, None

        daily_change_percent = (
            (current_price - previous_close) / previous_close
        ) * 100

        if not math.isfinite(daily_change_percent):
            return None, None

        return current_price, round(daily_change_percent, 2)

    except Exception:

        # Fallback: use the latest available daily history

        try:
            history = yf.Ticker(provider_symbol).history(period="5d")

            if history.empty or len(history) < 2:
                return None, None

            current_price = float(history["Close"].iloc[-1])
            previous_close = float(history["Close"].iloc[-2])

            if (
                not math.isfinite(current_price)
                or not math.isfinite(previous_close)
                or previous_close == 0
            ):
                return None, None

            daily_change_percent = (
                (current_price - previous_close) / previous_close
            ) * 100

            if not math.isfinite(daily_change_percent):
                return None, None

            return current_price, round(daily_change_percent, 2)

        except Exception:
            return None, None


# --------------------------------------------------
# GET USER WATCHLIST
# --------------------------------------------------

@router.get("", response_model=list[SavedStockResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    saved_stocks = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id
        )
        .order_by(SavedStock.created_at.desc())
        .all()
    )

    results = []

    for saved_stock in saved_stocks:

        current_price, daily_change_percent = get_stock_price(
            saved_stock.ticker,
            saved_stock.market
        )

        results.append({
            "saved_stock_id": saved_stock.saved_stock_id,
            "ticker": saved_stock.ticker,
            "market": saved_stock.market,
            "created_at": saved_stock.created_at,
            "current_price": current_price,
            "daily_change_percent": daily_change_percent
        })

    return results


# --------------------------------------------------
# ADD STOCK TO WATCHLIST
# --------------------------------------------------

@router.post(
    "",
    response_model=SavedStockResponse,
    status_code=status.HTTP_201_CREATED
)
def add_to_watchlist(
    data: SavedStockCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Validate CSRF token before changing data
    validate_csrf(request)

    ticker = data.ticker.strip().upper()
    market = normalize_market(data.market)

    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid stock ticker"
        )

    existing_stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == ticker,
            SavedStock.market == market
        )
        .first()
    )

    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stock is already in your watchlist for this market"
        )

    saved_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker,
        market=market
    )

    try:
        db.add(saved_stock)
        db.commit()
        db.refresh(saved_stock)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stock is already in your watchlist for this market"
        )

    return saved_stock


# --------------------------------------------------
# REMOVE STOCK FROM WATCHLIST
# --------------------------------------------------

@router.delete("/{saved_stock_id}")
def remove_from_watchlist(
    saved_stock_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Validate CSRF token before changing data
    validate_csrf(request)

    saved_stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id
        )
        .first()
    )

    if not saved_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved stock not found"
        )

    db.delete(saved_stock)
    db.commit()

    return {
        "message": "Stock removed from watchlist successfully"
    }
