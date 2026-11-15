import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ResearchTask, ResearchReport, AgentResult, SourceDocument
from app.schemas import (
    ResearchTaskCreate, 
    ResearchTaskResponse,
    ResearchReportResponse,
    AgentResultResponse,
    SourceDocumentResponse
)
from app.dependencies import get_current_user
from app.routers.stocks import STOCK_CATALOG
from app.services.agent_engine import (
    FundamentalAgent, 
    TechnicalAgent, 
    SentimentAgent, 
    RiskAgent, 
    LeadAnalystSynthesizer
)

router = APIRouter(tags=["Research Tasks & History"])

@router.get("/history", response_model=List[ResearchTaskResponse])
def get_research_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve past research tasks initiated by the logged-in user.
    User ID derived strictly from JWT.
    """
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )
    return tasks

@router.post("/tasks", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
def create_research_task(
    task_in: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Launch a new multi-agent research task for a stock ticker.
    Derives user_id directly from JWT.
    Executes Fundamental, Technical, Sentiment, and Risk agents and synthesizes the findings.
    """
    ticker_clean = task_in.ticker.strip().upper()
    
    # Retrieve current base price & company name
    matched = next((s for s in STOCK_CATALOG if s["ticker"] == ticker_clean), None)
    base_price = matched["base_price"] if matched else 1500.00
    company_name = matched["name"] if matched else f"{ticker_clean} Corporation"

    # 1. Fundamental Agent
    fundamental_report = FundamentalAgent.analyze(ticker_clean, task_in.market, base_price)

    # 2. Technical Agent
    technical_report = TechnicalAgent.analyze(ticker_clean, base_price, task_in.requested_period)

    # 3. Sentiment Agent
    sentiment_report = SentimentAgent.analyze(ticker_clean, task_in.market)

    # 4. Risk Management Agent
    risk_report = RiskAgent.analyze(ticker_clean, base_price, task_in.market)

    # 5. Lead Analyst Synthesizer
    synthesis = LeadAnalystSynthesizer.synthesize(
        ticker=ticker_clean,
        market=task_in.market,
        period=task_in.requested_period,
        current_price=base_price,
        fundamental=fundamental_report,
        technical=technical_report,
        sentiment=sentiment_report,
        risk=risk_report
    )

    now = datetime.utcnow()
    new_task = ResearchTask(
        user_id=current_user.user_id,
        ticker=ticker_clean,
        company_name=company_name,
        market=task_in.market,
        requested_period=task_in.requested_period,
        status="Completed",
        created_at=now,
        completed_at=now,
        summary=synthesis["executive_summary"],
        recommendation=synthesis["recommendation"],
        target_price=synthesis["target_price"],
        report_json=json.dumps(synthesis)
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Create associated ResearchReport record
    research_report = ResearchReport(
        task_id=new_task.task_id,
        consolidated_report=json.dumps(synthesis),
        summary=synthesis["executive_summary"],
        limitations="Past performance and algorithmic estimates are not indicative of future returns. Verify with a certified financial advisor before trading.",
        created_at=now
    )
    db.add(research_report)

    # Create AgentResult records for each autonomous agent
    agent_entries = [
        ("Fundamental Agent", fundamental_report),
        ("Technical Agent", technical_report),
        ("Sentiment Agent", sentiment_report),
        ("Risk Management Agent", risk_report),
        ("Lead Analyst Synthesizer", synthesis)
    ]
    for agent_name, out_data in agent_entries:
        agent_res = AgentResult(
            task_id=new_task.task_id,
            agent_name=agent_name,
            status="Completed",
            structured_output=json.dumps(out_data),
            error_message=None,
            created_at=now
        )
        db.add(agent_res)

    # Create SourceDocument records
    sources = [
        (
            f"{ticker_clean} Exchange Filings & Corporate Governance Disclosures",
            f"https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol={ticker_clean}"
        ),
        (
            f"{ticker_clean} Market Order Book & Historical OHLCV Series",
            f"https://www.nseindia.com/get-quotes/equity?symbol={ticker_clean}"
        ),
        (
            f"{ticker_clean} Financial Press Releases & Sentiment News Feed",
            f"https://finance.yahoo.com/quote/{ticker_clean}"
        )
    ]
    for title, url in sources:
        doc = SourceDocument(
            task_id=new_task.task_id,
            source_title=title,
            url=url,
            publication_time=now,
            retrieval_time=now
        )
        db.add(doc)

    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/tasks/{task_id}", response_model=ResearchTaskResponse)
def get_task_details(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full report and status for a specific research task.
    Enforces authorization - task must belong to authenticated user.
    """
    task = (
        db.query(ResearchTask)
        .filter(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == current_user.user_id
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found or unauthorized access."
        )
    return task

@router.get("/tasks/{task_id}/report", response_model=ResearchReportResponse)
def get_task_report(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve consolidated research report record for a completed task."""
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id, ResearchTask.user_id == current_user.user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")
    report = db.query(ResearchReport).filter(ResearchReport.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report record not found for this task.")
    return report

@router.get("/tasks/{task_id}/agents", response_model=List[AgentResultResponse])
def get_task_agents(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve individual agent results for a completed task."""
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id, ResearchTask.user_id == current_user.user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")
    return db.query(AgentResult).filter(AgentResult.task_id == task_id).all()

@router.get("/tasks/{task_id}/sources", response_model=List[SourceDocumentResponse])
def get_task_sources(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve verified source documents for a completed task."""
    task = db.query(ResearchTask).filter(ResearchTask.task_id == task_id, ResearchTask.user_id == current_user.user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")
    return db.query(SourceDocument).filter(SourceDocument.task_id == task_id).all()

