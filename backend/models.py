
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
    JSON,
)

from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------
# COMMON TIMESTAMP HELPER
# ---------------------------------------------------------

def utc_now():
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------
# 1. USERS
# ---------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Integer,
        primary_key=True
    )

    full_name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    preference = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    watchlists = relationship(
    "Watchlist",
    back_populates="user",
    cascade="all, delete-orphan"
)

    research_tasks = relationship(
        "ResearchTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ---------------------------------------------------------
# 2. USER PREFERENCES
# ---------------------------------------------------------

class UserPreference(Base):
    __tablename__ = "user_preferences"

    pref_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    preferred_market = Column(
        String(20),
        default="NSE",
        nullable=False
    )

    default_period = Column(
        String(10),
        default="1y",
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="preference"
    )


# ---------------------------------------------------------
# 3. RESEARCH TASKS
# ---------------------------------------------------------

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    ticker = Column(
        String(30),
        nullable=False,
        index=True
    )

    market = Column(
        String(20),
        nullable=False
    )

    requested_period = Column(
        String(10),
        nullable=False
    )

    status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="research_tasks"
    )

    agent_results = relationship(
        "AgentResult",
        back_populates="research_task",
        cascade="all, delete-orphan"
    )

    source_documents = relationship(
        "SourceDocument",
        back_populates="research_task",
        cascade="all, delete-orphan"
    )

    research_reports = relationship(
        "ResearchReport",
        back_populates="research_task",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_research_user_created",
            "user_id",
            "created_at"
        ),
    )


# ---------------------------------------------------------
# 4. AGENT RESULTS
# ---------------------------------------------------------

class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        Integer,
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False
    )

    agent_type = Column(
        String(50),
        nullable=False
    )

    status = Column(
        String(20),
        default="PENDING",
        nullable=False
    )

    summary = Column(
        Text,
        nullable=True
    )

    result_data = Column(
        JSON,
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    research_task = relationship(
        "ResearchTask",
        back_populates="agent_results"
    )

    __table_args__ = (
        Index(
            "ix_agent_results_task_type",
            "task_id",
            "agent_type"
        ),
    )


# ---------------------------------------------------------
# 5. SOURCE DOCUMENTS
# ---------------------------------------------------------

class SourceDocument(Base):
    __tablename__ = "source_documents"

    source_id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        Integer,
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False
    )

    source_type = Column(
        String(50),
        nullable=False
    )

    title = Column(
        String(500),
        nullable=False
    )

    url = Column(
        Text,
        nullable=True
    )

    publisher = Column(
        String(255),
        nullable=True
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    retrieved_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    content_summary = Column(
        Text,
        nullable=True
    )

    metadata_json = Column(
        JSON,
        nullable=True
    )

    research_task = relationship(
        "ResearchTask",
        back_populates="source_documents"
    )

    __table_args__ = (
        Index(
            "ix_source_documents_task",
            "task_id"
        ),
    )


# ---------------------------------------------------------
# 6. RESEARCH REPORTS
# ---------------------------------------------------------

class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(
        Integer,
        primary_key=True
    )

    task_id = Column(
        Integer,
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    executive_summary = Column(
        Text,
        nullable=True
    )

    report_data = Column(
        JSON,
        nullable=True
    )

    generated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    research_task = relationship(
        "ResearchTask",
        back_populates="research_reports"
    )

    __table_args__ = (
        Index(
            "ix_research_reports_task",
            "task_id"
        ),
    )

# ---------------------------------------------------------
# 7. WATCHLISTS
# ---------------------------------------------------------

class Watchlist(Base):
    __tablename__ = "watchlists"

    watchlist_id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="watchlists"
    )

    stocks = relationship(
        "SavedStock",
        back_populates="watchlist",
        cascade="all, delete-orphan"
    )

# ---------------------------------------------------------
# 7. SAVED STOCKS / WATCHLIST
# ---------------------------------------------------------

# ---------------------------------------------------------
# 8. SAVED STOCKS
# ---------------------------------------------------------

class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(
        Integer,
        primary_key=True
    )

    watchlist_id = Column(
        Integer,
        ForeignKey("watchlists.watchlist_id", ondelete="CASCADE"),
        nullable=False
    )

    ticker = Column(
        String(30),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    watchlist = relationship(
        "Watchlist",
        back_populates="stocks"
    )

    __table_args__ = (
        UniqueConstraint(
            "watchlist_id",
            "ticker",
            name="uq_watchlist_saved_ticker"
        ),
    )
