
import datetime
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv

# Load environment variables BEFORE importing application modules
load_dotenv()

import yfinance as yf
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import auth
import database
import models
import schemas



# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "Multi-Agent Stock Research Analyst"

# Configure this environment variable with comma-separated
# frontend origins, e.g. http://localhost:5173
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title=APP_NAME,
    description="Backend API for stock research, market data and user workspaces.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

@app.on_event("startup")
def initialize_database():
    """
    Create database tables that do not already exist.

    For a production deployment, use Alembic migrations
    instead of relying on create_all().
    """
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database initialized successfully.")


# ---------------------------------------------------------
# CONSTANTS AND HELPERS
# ---------------------------------------------------------

ALLOWED_MARKETS = {"NSE", "BSE", "US"}

ALLOWED_PERIODS = {
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max",
}

TICKER_PATTERN = re.compile(r"^[A-Za-z0-9.^=_-]{1,20}$")


def get_or_create_preferences(db: Session, user_id: int):
    """Retrieve a user's preferences or create default preferences."""

    preferences = (
        db.query(models.UserPreference)
        .filter(models.UserPreference.user_id == user_id)
        .first()
    )

    if preferences is None:
        preferences = models.UserPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


def normalize_ticker(ticker: str, market: str) -> str:
    """
    Convert a user-entered ticker into a Yahoo Finance symbol.

    NSE: RELIANCE -> RELIANCE.NS
    BSE: RELIANCE -> RELIANCE.BO
    US:  AAPL -> AAPL
    """

    ticker = ticker.strip().upper()
    market = market.strip().upper()

    if not ticker or not TICKER_PATTERN.fullmatch(ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid stock ticker."
        )

    if market not in ALLOWED_MARKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported market. Choose NSE, BSE or US."
        )

    if market == "NSE":
        if ticker.endswith(".BO"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A BSE ticker cannot be used with the NSE market."
            )
        if not ticker.endswith(".NS"):
            ticker += ".NS"

    elif market == "BSE":
        if ticker.endswith(".NS"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An NSE ticker cannot be used with the BSE market."
            )
        if not ticker.endswith(".BO"):
            ticker += ".BO"

    return ticker


def update_task_status(
    db: Session,
    task,
    task_status: str,
    completed: bool = False
):
    """Update and persist the status of a research task."""

    task.status = task_status

    if completed:
        task.completed_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()


# ---------------------------------------------------------
# GENERAL / HEALTH ENDPOINTS
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": f"{APP_NAME} API is running.",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

@app.post(
    "/api/auth/register",
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: schemas.UserRegister,
    db: Session = Depends(database.get_db)
):
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    try:
        new_user = models.User(
            full_name=user_data.full_name,
            email=user_data.email,
            password_hash=auth.hash_password(user_data.password)
        )

        db.add(new_user)
        db.flush()

        preferences = models.UserPreference(
            user_id=new_user.user_id
        )

        db.add(preferences)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully."
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during user registration.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register your account."
        )


@app.post(
    "/api/auth/login",
    response_model=schemas.TokenResponse
)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username)
        .first()
    )

    if not user or not auth.verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth.create_access_token(
        data={"user_id": user.user_id}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ---------------------------------------------------------
# USER WORKSPACE / PREFERENCES
# ---------------------------------------------------------

@app.get("/api/workspace/preferences")
def get_preferences(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return get_or_create_preferences(
        db,
        current_user.user_id
    )


@app.put("/api/workspace/preferences")
def update_preferences(
    pref_data: schemas.PreferenceUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    preferences = get_or_create_preferences(
        db,
        current_user.user_id
    )

    preferences.preferred_market = pref_data.preferred_market.upper()
    preferences.default_period = pref_data.default_period

    try:
        db.commit()
        db.refresh(preferences)

        return {
    "message": "Preferences updated successfully.",
    "preferred_market": preferences.preferred_market,
    "default_period": preferences.default_period
}

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to update user preferences.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update preferences."
        )


@app.get("/api/workspace/history")
def get_research_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    history = (
        db.query(models.ResearchTask)
        .filter(models.ResearchTask.user_id == current_user.user_id)
        .order_by(models.ResearchTask.created_at.desc())
        .all()
    )

    return history


# ---------------------------------------------------------
# WATCHLIST
# ---------------------------------------------------------

@app.get("/api/watchlist")
def get_watchlist(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return (
        db.query(models.SavedStock)
        .filter(models.SavedStock.user_id == current_user.user_id)
        .order_by(models.SavedStock.ticker.asc())
        .all()
    )


@app.post(
    "/api/watchlist",
    status_code=status.HTTP_201_CREATED
)
def add_to_watchlist(
    stock: schemas.WatchlistAdd,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    ticker = stock.ticker.strip().upper()

    if not ticker or not TICKER_PATTERN.fullmatch(ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid stock ticker."
        )

    duplicate = (
        db.query(models.SavedStock)
        .filter(
            models.SavedStock.user_id == current_user.user_id,
            models.SavedStock.ticker == ticker
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stock is already in your watchlist."
        )

    new_stock = models.SavedStock(
        user_id=current_user.user_id,
        ticker=ticker
    )

    try:
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)

        return {
            "message": f"{ticker} added to your watchlist successfully."
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stock is already in your watchlist."
        )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to add stock to watchlist.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update your watchlist."
        )


@app.delete("/api/watchlist/{ticker}")
def remove_from_watchlist(
    ticker: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    ticker = ticker.strip().upper()

    stock_item = (
        db.query(models.SavedStock)
        .filter(
            models.SavedStock.user_id == current_user.user_id,
            models.SavedStock.ticker == ticker
        )
        .first()
    )

    if not stock_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in your watchlist."
        )

    try:
        db.delete(stock_item)
        db.commit()

        return {
            "message": "Stock removed from your watchlist successfully."
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to remove stock from watchlist.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update your watchlist."
        )


# ---------------------------------------------------------
# MARKET DATA / STOCK SEARCH
# ---------------------------------------------------------

@app.get("/api/market/search")
def search_stock(
    ticker: str,
    market: str = "NSE",
    period: str = "1y",
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Search for a stock and retrieve historical market data.

    Returns:
    - Research task ID
    - Ticker and company name
    - Historical OHLCV data (latest 50 records)
    """

    market = market.strip().upper()
    period = period.strip().lower()

    if period not in ALLOWED_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported historical period. "
                "Choose 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd or max."
            )
        )

    yahoo_ticker = normalize_ticker(ticker, market)

    # Create a research task before retrieving market data.
    task = models.ResearchTask(
        user_id=current_user.user_id,
        ticker=yahoo_ticker,
        market=market,
        requested_period=period,
        status="PROCESSING"
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not create research task.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start stock research."
        )

    try:
        stock = yf.Ticker(yahoo_ticker)

        history = stock.history(
            period=period,
            auto_adjust=False
        )

        if history.empty:
            update_task_status(db, task, "FAILED")

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"No historical market data was found for "
                    f"{yahoo_ticker}."
                )
            )

        required_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in history.columns
        ]

        if missing_columns:
            update_task_status(db, task, "FAILED")

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The market data provider returned incomplete data."
            )

        history = history.dropna(subset=required_columns)

        if history.empty:
            update_task_status(db, task, "FAILED")

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No valid historical price records were found."
            )

        # Select the most recent 50 records.

        # Format historical records for the frontend.
        def format_history(dataframe):
            formatted = []

            for date, row in dataframe.iterrows():
                formatted.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"])
                })

            return formatted

        chart_data = format_history(history)
        formatted_history = format_history(history.tail(50))

        summary = {
            "first_date": history.index[0].strftime("%Y-%m-%d"),
            "latest_date": history.index[-1].strftime("%Y-%m-%d"),
            "total_records": len(history)
        }


# Company information is supplementary.
        # A failure here should not invalidate valid price data.
        company_name = yahoo_ticker

        try:
            company_info = stock.info
            company_name = (
                company_info.get("longName")
                or company_info.get("shortName")
                or yahoo_ticker
            )
        except Exception:
            logger.warning(
                "Could not retrieve company information for %s.",
                yahoo_ticker
            )

        update_task_status(
            db,
            task,
            "COMPLETED",
            completed=True
        )


        return {
    "task_id": task.task_id,
    "ticker": yahoo_ticker,
    "company_name": company_name,
    "market": market,
    "period": period,
    "summary": summary,
    "chart_data": chart_data,
    "historical_data": formatted_history
        }


    except HTTPException:
        # Preserve intentional HTTP errors such as 422 and 502.
        raise

    except Exception:
        try:
            db.rollback()
            task.status = "FAILED"
            db.commit()
        except SQLAlchemyError:
            db.rollback()

        logger.exception(
            "Market data retrieval failed for %s.",
            yahoo_ticker
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to retrieve stock data from the market "
                "data provider. Please try again later."
            )
        )