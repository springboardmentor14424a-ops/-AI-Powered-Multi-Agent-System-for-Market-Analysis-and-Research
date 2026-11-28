
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.research_task import ResearchTask
from app.services.stock_data_service import get_stock_analysis


# Convert ticker according to selected market
def prepare_stock_symbol(ticker: str, market: str) -> str:

    ticker = ticker.strip().upper()

    if "." in ticker or ticker.startswith("^"):
        return ticker

    if market == "NSE":
        return ticker + ".NS"

    if market == "BSE":
        return ticker + ".BO"

    return ticker


# Execute stock research
def execute_research_task(
    task_id: int,
    user_id: int,
    db: Session
):

    # Step 1: Find research task
    task = (
        db.query(ResearchTask)
        .filter(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == user_id
        )
        .first()
    )

    if task is None:
        return None

    # Step 2: Change status to Processing
    task.status = "Processing"
    task.completed_at = None

    try:
        db.commit()
        db.refresh(task)

        # Step 3: Prepare stock symbol
        symbol = prepare_stock_symbol(
            task.ticker,
            task.market
        )

        # Step 4: Fetch stock data and perform analysis
        analysis = get_stock_analysis(
            symbol=symbol,
            period=task.requested_period
        )

        # Step 5: Save analysis summary
        task.report = {
            "symbol": analysis["symbol"],
            "period": analysis["period"],
            "summary": analysis["summary"]
        }

        # Step 6: Mark task as Completed
        task.status = "Completed"
        task.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(task)

        return task

    except Exception as error:

        # Step 7: Mark task as Failed
        db.rollback()

        task = (
            db.query(ResearchTask)
            .filter(
                ResearchTask.task_id == task_id,
                ResearchTask.user_id == user_id
            )
            .first()
        )

        if task is not None:
            task.status = "Failed"
            task.completed_at = datetime.now(timezone.utc)
            task.report = {
                "error": str(error)
            }

            db.commit()
            db.refresh(task)

        return task
