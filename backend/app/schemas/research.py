
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from uuid import UUID


class ResearchTaskCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    ticker: str = Field(min_length=1, max_length=20)
    market: str = Field(min_length=1, max_length=100)
    analysis_period: str = Field(min_length=1, max_length=100)


class ResearchTaskResponse(BaseModel):
    task_id: UUID
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    started_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ResearchReportResponse(BaseModel):
    report_id: UUID
    task_id: UUID
    report_content: str
    summary: str | None = None
    limitations: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
