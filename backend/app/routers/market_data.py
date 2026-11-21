"""Stock search and market data (Module 2): search, OHLCV history, company profile,
financial statements, with sources, retrieval times and data-quality checks."""
import logging

import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import DataRetrieval, User
from ..schemas import AnalysisPeriod, Market, normalise_ticker
from ..stocks import PERIOD_DAYS, find_stock, provider_symbol, search_stocks
from ..data import DataUnavailable, company, prices, validation
from ..data.search import live_search

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market data"])


def _ticker(market: str, raw: str) -> str:
    try:
        return normalise_ticker(market, raw)
    except ValueError as e:
        raise HTTPException(422, str(e))


def _unavailable(e: DataUnavailable):
    return HTTPException(503, f"{e}")


def _record(db: Session, user: User, market, ticker, dataset, source, retrieved_at, from_cache, rows=None, quality=None):
    """Remember what was served. Same dataset retrieved at the same moment is stored once."""
    dup = db.scalar(
        select(DataRetrieval.id).where(
            DataRetrieval.user_id == user.id, DataRetrieval.market == market,
            DataRetrieval.ticker == ticker, DataRetrieval.dataset == dataset,
            DataRetrieval.retrieved_at == retrieved_at,
        )
    )
    if dup is not None:
        return
    db.add(DataRetrieval(user_id=user.id, market=market, ticker=ticker, dataset=dataset,
                         source=source[:200], retrieved_at=retrieved_at, from_cache=from_cache,
                         rows=rows, quality_status=quality))
    db.commit()


@router.get("/search")
def search(
    q: str = Query(min_length=1, max_length=50),
    market: Market | None = None,
    user: User = Depends(get_current_user),
):
    """Find companies by name or ticker: the built-in list first, then Yahoo Finance search."""
    results = [{**s, "source": "Built-in stock list"} for s in search_stocks(q, market)]
    seen = {(s["market"], s["ticker"]) for s in results}
    if len(results) < 10:
        for s in live_search(q, market):
            if (s["market"], s["ticker"]) not in seen:
                results.append({**s, "source": "Yahoo Finance search"})
                seen.add((s["market"], s["ticker"]))
    return results[:10]


@router.get("/{market}/{ticker}/prices")
def price_history(
    market: Market,
    ticker: str,
    period: AnalysisPeriod = "1 year",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticker = _ticker(market, ticker)
    days = PERIOD_DAYS[period]
    try:
        data = prices.get_prices(market, ticker, days)
    except DataUnavailable as e:
        raise _unavailable(e)

    frame = data.frame[data.frame.index >= data.frame.index[-1] - pd.Timedelta(days=days)]
    quality = validation.validate_prices(frame, data.cleaning)
    flagged = quality.pop("flagged")

    rows = []
    for d, r in frame.iterrows():
        key = d.strftime("%Y-%m-%d")
        rows.append({
            "date": key,
            "open": _round(r["open"]), "high": _round(r["high"]),
            "low": _round(r["low"]), "close": _round(r["close"]),
            "volume": None if r["volume"] != r["volume"] else int(r["volume"]),
            "flag": flagged.get(key),
        })
    stock = find_stock(market, ticker)
    provenance = {
        "source": data.source, "symbol": data.symbol, "retrieved_at": data.retrieved_at,
        "from_cache": data.from_cache, "rows": len(rows),
        "first_date": quality["first_date"], "last_date": quality["last_date"],
    }
    _record(db, user, market, ticker, "prices", data.source, data.retrieved_at, data.from_cache,
            len(rows), quality["status"])
    return {
        "market": market, "ticker": ticker, "company_name": stock["company_name"] if stock else None,
        "period": period, "provenance": provenance, "quality": quality, "rows": rows,
    }


def _round(x):
    return None if x != x else round(float(x), 4)


@router.get("/{market}/{ticker}/profile")
def profile(market: Market, ticker: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticker = _ticker(market, ticker)
    try:
        c = company.get_profile(market, ticker)
    except DataUnavailable as e:
        raise _unavailable(e)
    _record(db, user, market, ticker, "profile", c.source, c.retrieved_at, c.from_cache)
    return {"market": market, "ticker": ticker, "symbol": provider_symbol(market, ticker),
            "profile": c.payload, "provenance": _prov(c), "notes": c.notes}


@router.get("/{market}/{ticker}/financials")
def financials(market: Market, ticker: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticker = _ticker(market, ticker)
    try:
        c = company.get_statements(market, ticker)
    except DataUnavailable as e:
        raise _unavailable(e)
    _record(db, user, market, ticker, "financials", c.source, c.retrieved_at, c.from_cache)
    return {"market": market, "ticker": ticker, "statements": c.payload,
            "provenance": _prov(c), "notes": c.notes}


def _prov(c) -> dict:
    return {"source": c.source, "retrieved_at": c.retrieved_at, "from_cache": c.from_cache}


@router.get("/retrievals")
def my_retrievals(limit: int = Query(50, ge=1, le=200), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """The logged-in user's own data-retrieval log, newest first."""
    rows = db.scalars(
        select(DataRetrieval).where(DataRetrieval.user_id == user.id)
        .order_by(DataRetrieval.created_at.desc(), DataRetrieval.id.desc()).limit(limit)
    ).all()
    return [
        {"id": r.id, "market": r.market, "ticker": r.ticker, "dataset": r.dataset, "source": r.source,
         "retrieved_at": r.retrieved_at, "from_cache": r.from_cache, "rows": r.rows,
         "quality_status": r.quality_status, "logged_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
