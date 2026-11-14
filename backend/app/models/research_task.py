
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    company_name = Column(
        String(255),
        nullable=False
    )

    ticker = Column(
        String(20),
        nullable=False
    )

    market = Column(
        String(100),
        nullable=False
    )

    analysis_period = Column(
        String(100),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING"
    )

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
