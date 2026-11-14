
from sqlalchemy import Column, Integer, String, DateTime,ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base




from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index
)


# Existing User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


# New Research Task model
class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    company_name = Column(String(150), nullable=False)
    stock_ticker = Column(String(20), nullable=False)
    market = Column(String(50), nullable=False)
    analysis_period = Column(String(50), nullable=False)

    research_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    status = Column(
        String(20),
        default="Pending",
        nullable=False
    )

    report_content = Column("research", Text, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_research_user_date", "user_id", "research_date"),
    )


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    company_name = Column(String(150), nullable=False)
    stock_ticker = Column(String(20), nullable=False)

    saved_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "stock_ticker",
            name="uq_user_saved_ticker"
        ),
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    market = Column(
        String(20),
        nullable=False,
        default="NASDAQ"
    )

    analysis_period = Column(
        String(30),
        nullable=False,
        default="3 Months"
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
