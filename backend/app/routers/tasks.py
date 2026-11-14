from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import time
from pydantic import BaseModel
from app.database import get_db, SessionLocal
from app.models import User, ResearchTask, UserPreference, ResearchReport
from app.schemas import ResearchTaskResponse, ResearchTaskCreate
from app.dependencies import get_current_user
from app.services.market_data import get_historical_dataset, format_ticker_for_market, DEFAULT_TICKERS

class TaskStatusUpdate(BaseModel):
    status: str

router = APIRouter(prefix="/api/tasks", tags=["Research History & Tasks"])

def execute_research_pipeline(task_id: str, ticker: str, market: str, period: str):
    """
    Background worker that executes the research pipeline asynchronously:
    1. Transitions task status from Pending -> Processing
    2. Dynamically queries Yahoo Finance market data and company fundamentals
    3. Generates the comprehensive research dossier
    4. Transitions task status to Completed (or Failed if error occurs)
    """
    with SessionLocal() as db:
        task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id).first()
        if not task:
            return

        task.status = "Processing"
        db.commit()

        try:
            # Brief pause so status progression (Pending -> Processing -> Completed) is clearly observable
            time.sleep(1.0)

            hist_data = get_historical_dataset(ticker, market, period)
            total_days = hist_data.get("total_trading_days", 0)
            ret_pct = hist_data.get("period_return_pct", 0.0)
            symbol_used = hist_data.get("formatted_symbol", ticker)
            error_msg = hist_data.get("error")

            if error_msg or (total_days == 0 and not hist_data.get("recent_ohlcv")):
                task.status = "Failed"
                task.completed_at = datetime.now(timezone.utc)
                failed_summary = f"Unable to retrieve market dataset from Yahoo Finance for {symbol_used} ({market}). Error: {error_msg or 'No trading records available'}"
                err_report = ResearchReport(
                    task_id=task.task_id,
                    summary=failed_summary,
                    report_content=f"### Research Task Failed\n\n- **Symbol**: `{symbol_used}`\n- **Exchange**: {market}\n- **Period**: {period}\n- **Status**: Failed\n\nCould not retrieve historical data for the requested symbol. Please verify the stock ticker and exchange.",
                    limitations="Historical data query failed or symbol is not actively traded on the specified exchange.",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(err_report)
                db.commit()
                return

            summary_text = (
                f"Dynamic market dataset retrieved from Yahoo Finance for {symbol_used} ({market}) "
                f"covering {period}. Dataset contains {total_days} active trading days "
                f"({hist_data.get('start_date', 'N/A')} to {hist_data.get('end_date', 'N/A')}). "
                f"Period Return: {ret_pct:+.2f}%. Period High: {hist_data.get('highest_price', 'N/A')}, Low: {hist_data.get('lowest_price', 'N/A')}."
            )

            recent_table_lines = [
                f" - {r['date']}: Open {r['open']} | High {r['high']} | Low {r['low']} | Close {r['close']} | Vol {r['volume']:,}"
                for r in hist_data.get("recent_ohlcv", [])
            ]
            recent_ohlcv_str = "\n".join(recent_table_lines) if recent_table_lines else "No trading sessions recorded."

            sector = hist_data.get("sector", "General Equities")
            industry = hist_data.get("industry", "Diversified Operations")
            curr = hist_data.get("currency", "USD")
            mkt_cap = hist_data.get("market_cap", 0)
            trailing_pe = hist_data.get("trailing_pe")
            forward_pe = hist_data.get("forward_pe")
            eps = hist_data.get("trailing_eps")
            target_price = hist_data.get("target_mean_price")
            rec = hist_data.get("recommendation_key", "N/A")
            f_fifty = hist_data.get("fifty_day_avg")
            f_two_hundred = hist_data.get("two_hundred_day_avg")
            y_high = hist_data.get("fifty_two_week_high")
            y_low = hist_data.get("fifty_two_week_low")

            mkt_cap_str = f"{mkt_cap:,} {curr}" if mkt_cap else "N/A"
            pe_str = f"{trailing_pe:.2f}" if trailing_pe else "N/A"
            fwd_pe_str = f"{forward_pe:.2f}" if forward_pe else "N/A"
            eps_str = f"{eps:.2f} {curr}" if eps else "N/A"
            target_str = f"{target_price:.2f} {curr}" if target_price else "N/A"
            f_fifty_str = f"{f_fifty:.2f} {curr}" if f_fifty else "N/A"
            f_two_hundred_str = f"{f_two_hundred:.2f} {curr}" if f_two_hundred else "N/A"
            fifty_two_range = f"{y_low} - {y_high} {curr}" if (y_high and y_low) else "N/A"

            detailed_content = (
                f"### Comprehensive Equity Research Dossier\n\n"
                f"#### 1. Company & Asset Profile\n"
                f"- **Asset**: {task.company_name} (`{symbol_used}`)\n"
                f"- **Exchange Market**: {market}\n"
                f"- **Sector / Industry**: {sector} • {industry}\n"
                f"- **Market Capitalization**: {mkt_cap_str}\n\n"
                f"#### 2. Historical Price Performance ({period})\n"
                f"- **Analysis Window**: {period} ({hist_data.get('start_date', 'N/A')} to {hist_data.get('end_date', 'N/A')})\n"
                f"- **Total Trading Sessions**: {total_days} active trading days\n"
                f"- **Initial Price**: {hist_data.get('start_price', 'N/A')} {curr}\n"
                f"- **Latest Close Price**: {hist_data.get('end_price', 'N/A')} {curr}\n"
                f"- **Cumulative Period Return**: {ret_pct:+.2f}%\n"
                f"- **Period High / Low**: {hist_data.get('highest_price', 'N/A')} / {hist_data.get('lowest_price', 'N/A')} {curr}\n"
                f"- **Average Daily Volume**: {hist_data.get('average_daily_volume', 0):,} shares\n\n"
                f"#### 3. Key Valuation & Fundamental Indicators\n"
                f"- **Trailing P/E Ratio**: {pe_str}\n"
                f"- **Forward P/E Ratio**: {fwd_pe_str}\n"
                f"- **Trailing EPS (Earnings Per Share)**: {eps_str}\n"
                f"- **Wall Street Consensus Target**: {target_str}\n"
                f"- **Analyst Consensus Rating**: `{rec}`\n\n"
                f"#### 4. Technical Trend & Moving Averages\n"
                f"- **50-Day Moving Average**: {f_fifty_str}\n"
                f"- **200-Day Moving Average**: {f_two_hundred_str}\n"
                f"- **52-Week Range**: {fifty_two_range}\n\n"
                f"#### 5. Recent Trading Sessions (OHLCV Records):\n"
                f"{recent_ohlcv_str}\n\n"
                f"Data dynamically sourced via Yahoo Finance API (yfinance)."
            )

            new_report = ResearchReport(
                task_id=task.task_id,
                summary=summary_text,
                report_content=detailed_content,
                limitations="Historical price data subject to Yahoo Finance API query rate limits and exchange operational hours.",
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_report)

            task.status = "Completed"
            task.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            task.status = "Failed"
            task.completed_at = datetime.now(timezone.utc)
            err_report = ResearchReport(
                task_id=task.task_id,
                summary=f"Analysis pipeline error: {str(e)}",
                report_content=f"### Pipeline Error\n\nAn unexpected exception occurred: `{str(e)}`",
                limitations="Workflow aborted due to internal processing error.",
                created_at=datetime.now(timezone.utc)
            )
            db.add(err_report)
            db.commit()

@router.get("", response_model=List[ResearchTaskResponse])
def get_user_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only the logged-in user's research tasks, derived strictly from the verified JWT.
    """
    return db.query(ResearchTask).filter(
        ResearchTask.user_id == current_user.user_id
    ).order_by(ResearchTask.created_at.desc()).all()

@router.post("", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def start_research_task(
    task_in: ResearchTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    market = task_in.market
    period = task_in.requested_period or (prefs.default_analysis_period if prefs else "1 Year")
    raw_input = task_in.ticker.strip()
    ticker = raw_input.upper()
    company_name = task_in.company_name

    # Intelligent resolution: Match by ticker symbol OR company name
    matched = None
    for item in DEFAULT_TICKERS:
        if item["ticker"].upper() == ticker:
            matched = item
            break

    if not matched:
        lower_input = raw_input.lower()
        for item in DEFAULT_TICKERS:
            if item["name"].lower() == lower_input:
                matched = item
                break
        if not matched:
            for item in DEFAULT_TICKERS:
                if lower_input in item["name"].lower() or item["ticker"].lower() == lower_input:
                    matched = item
                    break

    if matched:
        ticker = matched["ticker"]
        company_name = company_name or matched["name"]
        if not market:
            market = matched["market"]
    elif not company_name:
        company_name = f"{ticker} Corporation"

    if not market:
        market = prefs.preferred_market if prefs else "NASDAQ"

    now = datetime.now(timezone.utc)
    new_task = ResearchTask(
        user_id=current_user.user_id,
        ticker=ticker,
        company_name=company_name,
        market=market,
        requested_period=period,
        status="Pending",  # Initialized as Pending
        created_at=now,
        completed_at=None
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Launch background research task for realistic, real-time status progression
    background_tasks.add_task(
        execute_research_pipeline,
        task_id=str(new_task.task_id),
        ticker=ticker,
        market=market,
        period=period
    )

    return new_task

@router.get("/{task_id}")
def get_task_report(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found or unauthorized"
        )

    report_row = db.query(ResearchReport).filter(ResearchReport.task_id == task.task_id).first()
    summary_text = report_row.summary if report_row else f"Initial summary for {task.ticker}"
    content_text = report_row.report_content if report_row else f"Initial analysis notes for {task.ticker}"
    limitations_text = report_row.limitations if report_row else "Subject to provider availability"

    return {
        "task_id": task.task_id,
        "ticker": task.ticker,
        "company_name": task.company_name,
        "market": task.market,
        "requested_period": task.requested_period,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "report": {
            "title": f"Initial Stock Research Summary: {task.ticker} ({task.market})",
            "period": task.requested_period,
            "analyst_notes": content_text,
            "summary": summary_text,
            "limitations": limitations_text,
            "metrics": {
                "market": task.market,
                "status": task.status,
                "requested_period": task.requested_period
            }
        }
    }

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes an individual research entry and its corresponding report from the database.
    Strictly verifies ownership: users can only delete their own research history entries.
    """
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research entry not found or unauthorized."
        )

    db.delete(task)
    db.commit()
    return None

@router.patch("/{task_id}/status", response_model=ResearchTaskResponse)
def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the research status of an individual research task.
    Allowed statuses: Pending, Processing, Completed, Failed.
    """
    allowed_statuses = ["Pending", "Processing", "Completed", "Failed"]
    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{payload.status}'. Allowed values are: {allowed_statuses}"
        )

    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research entry not found or unauthorized."
        )

    task.status = payload.status
    if payload.status in ["Completed", "Failed"]:
        task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task
