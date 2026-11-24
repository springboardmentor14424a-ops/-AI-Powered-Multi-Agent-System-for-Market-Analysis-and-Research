
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    func
)

from sqlalchemy.orm import relationship

from app.database import Base


# USERS TABLE
class User(Base):

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)

    full_name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    research_tasks = relationship(
        "ResearchTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    saved_stocks = relationship(
        "SavedStock",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


# USER PREFERENCES TABLE
class UserPreference(Base):

    __tablename__ = "user_preferences"

    preference_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    market = Column(
        String(30),
        nullable=False,
        default="NASDAQ"
    )

    research_period = Column(
        String(30),
        nullable=False,
        default="3M"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="preferences"
    )


# RESEARCH TASKS TABLE
class ResearchTask(Base):

    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    ticker = Column(String(30), nullable=False)

    market = Column(String(30), nullable=False)

    requested_period = Column(String(30), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="Pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="research_tasks"
    )

    research_report = relationship(
        "ResearchReport",
        back_populates="research_task",
        uselist=False,
        cascade="all, delete-orphan"
    )


# RESEARCH REPORTS TABLE
class ResearchReport(Base):

    __tablename__ = "research_reports"

    report_id = Column(Integer, primary_key=True, index=True)

    task_id = Column(
        Integer,
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    report_content = Column(Text, nullable=True)

    summary = Column(Text, nullable=True)

    limitations = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    research_task = relationship(
        "ResearchTask",
        back_populates="research_report"
    )


# SAVED STOCKS TABLE
class SavedStock(Base):

    __tablename__ = "saved_stocks"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            "market",
            name="uq_saved_stock_user_ticker_market"
        ),
    )

    saved_stock_id = Column(
        Integer,
        primary_key=True,
        index=True
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
        String(30),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="saved_stocks"
    )
