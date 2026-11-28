
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.sql import func

from app.database.database import Base


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    ticker = Column(
        String(30),
        nullable=False
    )

    market = Column(
        String(20),
        nullable=False
    )

    requested_period = Column(
        String(20),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="Pending"
    )

    # Store stock analysis report
    report = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
