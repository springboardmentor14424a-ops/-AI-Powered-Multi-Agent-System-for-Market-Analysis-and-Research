import math

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents.technical import rsi
from ..data import DataUnavailable, prices
from ..database import get_db
from ..deps import get_current_user
from ..models import PENDING, ResearchTask, User
from ..schemas import ResearchDetail, ResearchIn, ResearchSummary
from ..stocks import PERIOD_DAYS
from ..workflow import run_workflow

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=ResearchSummary, status_code=status.HTTP_201_CREATED)
def start_research(
    payload: ResearchIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # The owner is the user from the verified JWT, never anything in the request body.
    task = ResearchTask(
        user_id=user.id,
        company_name=payload.company_name,
        ticker=payload.ticker,
        market=payload.market,
        analysis_period=payload.analysis_period,
        status=PENDING,
    )
    db.add(task)
    db.commit()
    background.add_task(run_workflow, task.id)
    return task


@router.get("", response_model=list[ResearchSummary])
def list_research(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the logged-in user's tasks, newest first."""
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.user_id == user.id)
        .order_by(ResearchTask.created_at.desc(), ResearchTask.id.desc())
        .limit(200)
    )
    return db.scalars(stmt).all()


@router.get("/{task_id}", response_model=ResearchDetail)
def get_research(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Filtering by user_id too means another user's task looks exactly like a missing one.
    task = db.scalar(
        select(ResearchTask).where(ResearchTask.id == task_id, ResearchTask.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research task not found.")
    return task


def _val(x, digits=4):
    """JSON-safe number (NaN/inf -> None)."""
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else round(float(x), digits)


@router.get("/{task_id}/chart")
def research_chart(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Price history for the report's charts: OHLCV plus the indicators the Technical agent uses
    (moving averages, RSI, MACD), computed on the full history and then cut to the analysis window."""
    task = db.scalar(
        select(ResearchTask).where(ResearchTask.id == task_id, ResearchTask.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research task not found.")

    days = PERIOD_DAYS[task.analysis_period]
    try:
        data = prices.get_prices(task.market, task.ticker, days)
    except DataUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))

    df = data.frame
    close = df["close"]
    ind = pd.DataFrame({
        "sma20": close.rolling(20).mean(),
        "sma50": close.rolling(50).mean(),
        "sma200": close.rolling(200).mean(),
        "rsi": rsi(close),
    })
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    ind["macd"] = macd
    ind["macd_signal"] = macd.ewm(span=9, adjust=False).mean()
    ind["macd_hist"] = ind["macd"] - ind["macd_signal"]

    window = df.index >= df.index[-1] - pd.Timedelta(days=days)
    df, ind = df[window], ind[window]
    rows = []
    for d in df.index:
        r, i = df.loc[d], ind.loc[d]
        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "open": _val(r["open"]), "high": _val(r["high"]), "low": _val(r["low"]), "close": _val(r["close"]),
            "volume": None if r["volume"] != r["volume"] else int(r["volume"]),
            **{k: _val(i[k]) for k in ind.columns},
        })
    first, last = float(df["close"].iloc[0]), float(df["close"].iloc[-1])
    return {
        "symbol": data.symbol, "source": data.source, "retrieved_at": data.retrieved_at,
        "period": task.analysis_period, "rows": rows,
        "summary": {
            "start_date": rows[0]["date"], "end_date": rows[-1]["date"],
            "first_close": _val(first), "last_close": _val(last),
            "period_return": _val(last / first - 1, 6),
            "high": _val(float(df["high"].max())), "low": _val(float(df["low"].min())),
        },
    }
