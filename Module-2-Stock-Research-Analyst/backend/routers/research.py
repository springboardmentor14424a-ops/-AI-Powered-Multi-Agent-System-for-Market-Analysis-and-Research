from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from database.connection import get_db, AsyncSessionLocal
from models.user import User, ResearchTask, ResearchReport
from schemas.auth import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchTaskUpdate,
    ResearchReportResponse,
)

import httpx
import asyncio
import traceback
from datetime import datetime, timezone

router = APIRouter(prefix="/api/research", tags=["research"])


# ─── Helper: Fetch data from Yahoo Finance for report generation ─────────────

async def _fetch_yahoo_chart(ticker: str, period: str = "1y", interval: str = "1d"):
    """Fetch chart data for the ticker."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"range": period, "interval": interval}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return resp.json()
    return None


async def _fetch_yahoo_quote_summary(ticker: str):
    """Fetch quote summary (profile + financials) for the ticker."""
    modules = "assetProfile,defaultKeyStatistics,financialData,incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory"
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
    params = {"modules": modules}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Try to get crumb + cookies
        try:
            cr_resp = await client.get(
                "https://query2.finance.yahoo.com/v1/test/getcrumb",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if cr_resp.status_code == 200:
                crumb = cr_resp.text.strip()
                params["crumb"] = crumb
                cookies = dict(cr_resp.cookies)
                resp = await client.get(url, params=params, cookies=cookies, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        # Fallback: try without crumb
        try:
            resp = await client.get(url, params={"modules": modules}, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

    return None


def _generate_report_content(ticker: str, company_name: str, market: str, period: str,
                             chart_data: dict | None, summary_data: dict | None) -> str:
    """Generate a formatted research report from collected data."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Stock Research Report: {company_name} ({ticker})",
        f"**Market:** {market} | **Analysis Period:** {period}",
        f"**Generated:** {now}",
        f"**Data Source:** Yahoo Finance (Live API)",
        "",
        "---",
        "",
    ]

    # Price summary from chart data
    if chart_data:
        try:
            result = chart_data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            timestamps = result.get("timestamp", [])

            curr = meta.get("currency", "USD")
            sym = "₹" if curr == "INR" else "$"
            reg_price = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("chartPreviousClose", 0)

            closes = [c for c in (quotes.get("close") or []) if c is not None]
            highs = [h for h in (quotes.get("high") or []) if h is not None]
            lows = [l for l in (quotes.get("low") or []) if l is not None]
            volumes = [v for v in (quotes.get("volume") or []) if v is not None]

            lines.append("## 📊 Price Summary")
            lines.append(f"- **Current Price:** {sym}{reg_price:,.2f}")
            if prev_close:
                chg = reg_price - prev_close
                chg_pct = (chg / prev_close) * 100 if prev_close else 0
                direction = "📈" if chg >= 0 else "📉"
                lines.append(f"- **Period Change:** {direction} {sym}{chg:+,.2f} ({chg_pct:+.2f}%)")
            if highs:
                lines.append(f"- **Period High:** {sym}{max(highs):,.2f}")
            if lows:
                lines.append(f"- **Period Low:** {sym}{min(lows):,.2f}")
            if volumes:
                lines.append(f"- **Average Daily Volume:** {int(sum(volumes) / len(volumes)):,}")
                lines.append(f"- **Total Data Points:** {len(closes)} trading days")
            lines.append("")
        except Exception:
            lines.append("## 📊 Price Summary\n_Could not parse chart data._\n")

    # Company profile from summary
    if summary_data:
        try:
            qr = summary_data.get("quoteSummary", {}).get("result", [{}])[0]
            profile = qr.get("assetProfile", {})
            fin = qr.get("financialData", {})
            stats = qr.get("defaultKeyStatistics", {})

            if profile:
                lines.append("## 🏢 Company Profile")
                if profile.get("longBusinessSummary"):
                    summary_text = profile["longBusinessSummary"][:500]
                    if len(profile["longBusinessSummary"]) > 500:
                        summary_text += "..."
                    lines.append(f"{summary_text}")
                    lines.append("")
                if profile.get("sector"):
                    lines.append(f"- **Sector:** {profile['sector']}")
                if profile.get("industry"):
                    lines.append(f"- **Industry:** {profile['industry']}")
                if profile.get("fullTimeEmployees"):
                    lines.append(f"- **Employees:** {profile['fullTimeEmployees']:,}")
                if profile.get("city") or profile.get("country"):
                    loc = ", ".join(filter(None, [profile.get("city"), profile.get("country")]))
                    lines.append(f"- **Headquarters:** {loc}")
                lines.append("")

            if fin:
                lines.append("## 💰 Key Financial Metrics")
                curr = fin.get("financialCurrency", "USD")
                sym = "₹" if curr == "INR" else "$"
                for key, label in [
                    ("totalRevenue", "Total Revenue"),
                    ("revenueGrowth", "Revenue Growth"),
                    ("grossMargins", "Gross Margin"),
                    ("operatingMargins", "Operating Margin"),
                    ("profitMargins", "Profit Margin"),
                    ("returnOnEquity", "Return on Equity"),
                    ("currentRatio", "Current Ratio"),
                    ("debtToEquity", "Debt to Equity"),
                ]:
                    val = fin.get(key, {})
                    if isinstance(val, dict):
                        raw = val.get("raw")
                    else:
                        raw = val
                    if raw is not None:
                        if "Margin" in label or "Growth" in label or "Return" in label:
                            lines.append(f"- **{label}:** {raw * 100:.2f}%")
                        elif "Revenue" in label:
                            if raw >= 1e9:
                                lines.append(f"- **{label}:** {sym}{raw / 1e9:.2f}B")
                            elif raw >= 1e6:
                                lines.append(f"- **{label}:** {sym}{raw / 1e6:.2f}M")
                            else:
                                lines.append(f"- **{label}:** {sym}{raw:,.2f}")
                        else:
                            lines.append(f"- **{label}:** {raw:.2f}")
                lines.append("")

            if stats:
                lines.append("## 📈 Valuation Statistics")
                for key, label in [
                    ("trailingPE", "Trailing P/E"),
                    ("forwardPE", "Forward P/E"),
                    ("pegRatio", "PEG Ratio"),
                    ("priceToBook", "Price / Book"),
                    ("enterpriseToRevenue", "EV / Revenue"),
                    ("enterpriseToEbitda", "EV / EBITDA"),
                    ("beta", "Beta (5Y)"),
                ]:
                    val = stats.get(key, {})
                    if isinstance(val, dict):
                        raw = val.get("raw")
                    else:
                        raw = val
                    if raw is not None:
                        lines.append(f"- **{label}:** {raw:.2f}")
                lines.append("")

        except Exception:
            lines.append("## 🏢 Company Profile\n_Could not parse profile data._\n")

    if not chart_data and not summary_data:
        lines.append("## ⚠️ Data Collection Note")
        lines.append("Live data fetching encountered rate limits or connectivity issues.")
        lines.append("The research task has been completed with available data.")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report auto-generated by Multi-Agent Stock Research Analyst — {now}*")

    return "\n".join(lines)


# ─── Background task: auto-process research task ─────────────────────────────

async def _process_research_task(task_id: int):
    """Background task that transitions Pending → Processing → Completed."""
    async with AsyncSessionLocal() as db:
        try:
            # Get the task
            result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                return

            # Set to Processing
            task.status = "Processing"
            await db.commit()

            # Small delay to simulate processing
            await asyncio.sleep(1)

            # Determine period for Yahoo Finance
            period_map = {
                "1 Month": "1mo",
                "3 Months": "3mo",
                "6 Months": "6mo",
                "1 Year": "1y",
                "5 Years": "5y",
            }
            yf_period = period_map.get(task.analysis_period, "1y")

            # Fetch data concurrently
            chart_data, summary_data = await asyncio.gather(
                _fetch_yahoo_chart(task.ticker, period=yf_period),
                _fetch_yahoo_quote_summary(task.ticker),
                return_exceptions=True,
            )

            # Handle exceptions gracefully
            if isinstance(chart_data, Exception):
                chart_data = None
            if isinstance(summary_data, Exception):
                summary_data = None

            # Generate report
            report_content = _generate_report_content(
                ticker=task.ticker,
                company_name=task.company_name,
                market=task.market,
                period=task.analysis_period,
                chart_data=chart_data,
                summary_data=summary_data,
            )

            # Create report record
            report = ResearchReport(
                task_id=task.id,
                report_content=report_content,
            )
            db.add(report)

            # Set to Completed
            task.status = "Completed"
            await db.commit()

        except Exception as e:
            # On failure, set to Failed
            try:
                result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    task.status = "Failed"
                    await db.commit()
            except Exception:
                pass
            traceback.print_exc()


@router.post("/tasks", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: ResearchTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Create a new research task for the current user and auto-process it."""
    task = ResearchTask(
        user_id=current_user.id,
        company_name=payload.company_name,
        ticker=payload.ticker,
        market=payload.market,
        analysis_period=payload.analysis_period,
        status="Pending",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    task_id = task.id

    # Kick off background processing: Pending → Processing → Completed
    background_tasks.add_task(_process_research_task, task_id)

    return ResearchTaskResponse.model_validate(task)


@router.get("/tasks", response_model=list[ResearchTaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResearchTaskResponse]:
    """Return all research tasks for the current user, newest first."""
    result = await db.execute(
        select(ResearchTask)
        .where(ResearchTask.user_id == current_user.id)
        .order_by(ResearchTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=ResearchTaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Return a single research task (must belong to the current user)."""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this task.",
        )

    return ResearchTaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=ResearchTaskResponse)
async def update_task_status(
    task_id: int,
    payload: ResearchTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Update the status of a research task (must belong to the current user)."""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this task.",
        )

    task.status = payload.status
    await db.flush()
    await db.refresh(task)
    return ResearchTaskResponse.model_validate(task)


@router.get("/tasks/{task_id}/report", response_model=ResearchReportResponse)
async def get_task_report(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchReportResponse:
    """Return the research report for a task (must belong to the current user)."""
    # First verify the task belongs to the current user
    task_result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = task_result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this report.",
        )

    # Fetch the report
    report_result = await db.execute(
        select(ResearchReport).where(ResearchReport.task_id == task_id)
    )
    report: ResearchReport | None = report_result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for this task.",
        )

    return ResearchReportResponse.model_validate(report)
