import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SourceDocument, User, UserPreference
from ..schemas import (
    FinancialsOut, HistoryOut, Market, Period, ProfileOut, SearchResult, SourceOut,
)
from ..services import market_data
from ..services.market_data import NoDataError, ProviderError
from ..services.sources import record_source

router = APIRouter(prefix="/stocks", tags=["stocks"])

TICKER_RE = re.compile(r"[A-Za-z0-9.\-&^]{1,20}")


def _check_ticker(ticker: str):
    if not TICKER_RE.fullmatch(ticker):
        raise HTTPException(status_code=422, detail="Invalid ticker symbol")


def _preferences(db: Session, user: User):
    return db.get(UserPreference, user.user_id)


def _yahoo_url(symbol: str, page: str = "") -> str:
    return f"https://finance.yahoo.com/quote/{symbol}{page}"


@router.get("/search", response_model=list[SearchResult])
def search(
    q: str = Query(min_length=1, max_length=50),
    current_user: User = Depends(get_current_user),
):
    try:
        return market_data.search_stocks(q.strip())
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/sources/log", response_model=list[SourceOut])
def source_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(SourceDocument)
        .filter(SourceDocument.user_id == current_user.user_id)
        .order_by(SourceDocument.retrieved_at.desc())
        .limit(20)
        .all()
    )


@router.get("/{ticker}/history", response_model=HistoryOut)
def history(
    ticker: str,
    market: Market | None = None,
    period: Period | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_ticker(ticker)
    pref = _preferences(db, current_user)
    market = market or (pref.market if pref else "NSE")
    period = period or (pref.default_period if pref else "1Y")

    try:
        result = market_data.fetch_history(ticker, market, period)
    except NoDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record_source(
        db, current_user.user_id, "price_data",
        f"{result['symbol']} price history ({period})",
        _yahoo_url(result["symbol"], "/history"),
        result["prices"], result["retrieved_at"],
    )
    return result


@router.get("/{ticker}/profile", response_model=ProfileOut)
def profile(
    ticker: str,
    market: Market | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_ticker(ticker)
    pref = _preferences(db, current_user)
    market = market or (pref.market if pref else "NSE")

    try:
        result = market_data.fetch_profile(ticker, market)
    except NoDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record_source(
        db, current_user.user_id, "company_profile",
        f"{result['symbol']} company profile",
        _yahoo_url(result["symbol"], "/profile"),
        result["profile"], result["retrieved_at"],
    )
    return result


@router.get("/{ticker}/financials", response_model=FinancialsOut)
def financials(
    ticker: str,
    market: Market | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_ticker(ticker)
    pref = _preferences(db, current_user)
    market = market or (pref.market if pref else "NSE")

    try:
        result = market_data.fetch_financials(ticker, market)
    except NoDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record_source(
        db, current_user.user_id, "financial_statements",
        f"{result['symbol']} financial statements",
        _yahoo_url(result["symbol"], "/financials"),
        {
            "income": result["income_statement"],
            "balance": result["balance_sheet"],
            "cash": result["cash_flow"],
        },
        result["retrieved_at"],
    )
    return result