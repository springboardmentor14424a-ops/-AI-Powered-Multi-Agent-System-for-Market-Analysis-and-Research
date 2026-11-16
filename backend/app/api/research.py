from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.task import ResearchTask
from app.core.security import get_current_user
from app.services.research_agent import run_multi_agent_analysis

router = APIRouter(prefix="/api/research", tags=["Research"])

class ResearchRequest(BaseModel):
    ticker: str
    market: Optional[str] = "NSE"
    analysis_period: Optional[str] = "1 Year"

@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_research(payload: ResearchRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # Execute multi-agent live analysis
        report = run_multi_agent_analysis(payload.ticker, period="1y", risk_tolerance="Moderate")
        
        # Save research task record in database
        new_task = ResearchTask(
            user_id=current_user.id,
            ticker=payload.ticker.upper(),
            market=payload.market,
            analysis_period=payload.analysis_period,
            status="Completed",
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return {
            "message": "Research analysis completed successfully",
            "task_id": new_task.id,
            "report": report
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[dict])
def get_research_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(ResearchTask).filter(ResearchTask.user_id == current_user.id).order_by(ResearchTask.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "ticker": t.ticker,
            "market": t.market,
            "analysis_period": t.analysis_period,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]