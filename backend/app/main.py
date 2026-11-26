import secrets
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .fundamental_analysis import run_fundamental_analysis
from .market_data import YFinanceError, fetch_market_data, normalize_ticker, search_stocks
from .models import ResearchTask, SavedStock, User, UserPreference
from .schemas import (
    AnalysisPeriod,
    FundamentalAnalysisRequest,
    FundamentalAnalysisResponse,
    GoogleAuthRequest,
    LoginRequest,
    MarketCode,
    MarketDataResponse,
    RegistrationRequest,
    ResearchHistoryItem,
    ResearchReportResponse,
    SavedStockCreate,
    SavedStockResponse,
    StockSearchResponse,
    TokenResponse,
    UserResponse,
    UserPreferenceResponse,
    UserPreferenceUpdate,
)
from .security import create_access_token, get_user_id, hash_password, verify_password

app = FastAPI(title="Multi-Agent Stock Research Analyst - Fundamental Analysis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = db.get(User, get_user_id(request))
    if not user:
        raise HTTPException(status_code=401, detail="User account no longer exists")
    return user


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/auth/google/config")
def google_auth_config() -> dict[str, str | bool]:
    return {
        "enabled": bool(settings.google_client_id),
        "client_id": settings.google_client_id,
    }


@app.get("/api/stocks/search", response_model=StockSearchResponse)
def stock_search(
    q: str = Query(min_length=2, max_length=80),
    market: MarketCode = "US",
    _user: User = Depends(current_user),
) -> StockSearchResponse:
    try:
        return search_stocks(q, market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except YFinanceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/stocks/{ticker}/market-data", response_model=MarketDataResponse)
def stock_market_data(
    ticker: str,
    period: AnalysisPeriod = "1y",
    market: MarketCode = "US",
    _user: User = Depends(current_user),
) -> MarketDataResponse:
    try:
        return fetch_market_data(ticker, period, market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except YFinanceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/research/fundamental", response_model=FundamentalAnalysisResponse)
def fundamental_analysis(
    payload: FundamentalAnalysisRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> FundamentalAnalysisResponse:
    try:
        ticker = normalize_ticker(payload.ticker, payload.market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    task = ResearchTask(
        user_id=user.user_id,
        ticker=ticker,
        market=payload.market,
        requested_period=payload.period,
        status="running",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    try:
        result = run_fundamental_analysis(ticker, payload.period, payload.market)
        task.status = "completed"
        task.result_json = result.model_dump(mode="json")
        task.completed_at = datetime.utcnow()
        db.commit()
        return result
    except ValueError as error:
        task.status = "failed"
        task.error_message = str(error)
        task.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except YFinanceError as error:
        task.status = "failed"
        task.error_message = str(error)
        task.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/research/history", response_model=list[ResearchHistoryItem])
def research_history(
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[ResearchTask]:
    return list(
        db.scalars(
            select(ResearchTask)
            .where(ResearchTask.user_id == user.user_id)
            .order_by(ResearchTask.created_at.desc())
            .limit(limit)
        )
    )


@app.get("/api/research/history/{task_id}", response_model=ResearchReportResponse)
def research_report(
    task_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ResearchReportResponse:
    task = db.scalar(
        select(ResearchTask).where(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == user.user_id,
        )
    )
    if not task:
        raise HTTPException(status_code=404, detail="Research report not found")
    return ResearchReportResponse(
        task_id=task.task_id,
        ticker=task.ticker,
        market=task.market,
        requested_period=task.requested_period,
        status=task.status,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at,
        result=task.result_json,
    )


@app.get("/api/stocks/saved", response_model=list[SavedStockResponse])
def saved_stocks(
    watchlist_name: str | None = Query(default=None, max_length=60),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[SavedStock]:
    query = select(SavedStock).where(SavedStock.user_id == user.user_id)
    if watchlist_name:
        query = query.where(SavedStock.watchlist_name == watchlist_name)
    return list(db.scalars(query.order_by(SavedStock.created_at.desc())))


@app.post(
    "/api/stocks/saved",
    response_model=SavedStockResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_stock(
    payload: SavedStockCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SavedStock:
    try:
        ticker = normalize_ticker(payload.ticker, payload.market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    existing = db.scalar(
        select(SavedStock).where(
            SavedStock.user_id == user.user_id,
            SavedStock.ticker == ticker,
            SavedStock.watchlist_name == payload.watchlist_name,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="This stock is already in that watchlist")
    stock = SavedStock(
        user_id=user.user_id,
        ticker=ticker,
        market=payload.market,
        watchlist_name=payload.watchlist_name,
    )
    db.add(stock)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="This stock is already in that watchlist") from error
    db.refresh(stock)
    return stock


@app.delete("/api/stocks/saved/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_stock(
    saved_stock_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    stock = db.scalar(
        select(SavedStock).where(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == user.user_id,
        )
    )
    if not stock:
        raise HTTPException(status_code=404, detail="Saved stock not found")
    db.delete(stock)
    db.commit()


def _get_or_create_preferences(user_id: int, db: Session) -> UserPreference:
    preference = db.get(UserPreference, user_id)
    if preference:
        return preference
    preference = UserPreference(user_id=user_id)
    db.add(preference)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        preference = db.get(UserPreference, user_id)
        if preference:
            return preference
        raise
    db.refresh(preference)
    return preference


@app.get("/api/preferences", response_model=UserPreferenceResponse)
def get_preferences(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserPreference:
    return _get_or_create_preferences(user.user_id, db)


@app.put("/api/preferences", response_model=UserPreferenceResponse)
def update_preferences(
    payload: UserPreferenceUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserPreference:
    preference = _get_or_create_preferences(user.user_id, db)
    preference.market = payload.market
    preference.analysis_period = payload.analysis_period
    db.commit()
    db.refresh(preference)
    return preference


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegistrationRequest, db: Session = Depends(get_db)) -> User:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(UserPreference(user_id=user.user_id))
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return _create_session(user, response)


@app.post("/api/auth/google", response_model=TokenResponse)
def google_login(
    payload: GoogleAuthRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    try:
        claims = id_token.verify_oauth2_token(
            payload.credential,
            GoogleRequest(),
            audience=settings.google_client_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=401, detail="Invalid Google sign-in credential") from error
    except GoogleAuthError as error:
        raise HTTPException(status_code=502, detail="Google sign-in verification is temporarily unavailable") from error

    email = claims.get("email")
    if not claims.get("sub") or not isinstance(email, str) or claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google must provide a verified email address")

    normalized_email = email.lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if not user:
        full_name = str(claims.get("name") or normalized_email.split("@", 1)[0]).strip()[:120]
        user = User(
            full_name=full_name or "Google User",
            email=normalized_email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            user = db.scalar(select(User).where(User.email == normalized_email))
            if not user:
                raise HTTPException(status_code=409, detail="Could not create the Google account")
        else:
            db.add(UserPreference(user_id=user.user_id))
            db.commit()
            db.refresh(user)

    return _create_session(user, response)


def _create_session(user: User, response: Response) -> TokenResponse:
    token = create_access_token(user.user_id)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie("access_token")


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> User:
    return user
