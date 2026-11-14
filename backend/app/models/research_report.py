
import uuid

from sqlalchemy import Column, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    report_content = Column(
        Text,
        nullable=False
    )

    summary = Column(
        Text,
        nullable=True
    )

    limitations = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
