from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Float,
    Text,
    JSON,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    research_tasks: Mapped[List["ResearchTask"]] = relationship(
        "ResearchTask", back_populates="user", cascade="all, delete-orphan"
    )
    saved_stocks: Mapped[List["SavedStock"]] = relationship(
        "SavedStock", back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        "UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class ResearchTask(Base):
    __tablename__ = "research_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending','Processing','Completed','Failed')",
            name="chk_research_tasks_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_period: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="research_tasks")
    report: Mapped[Optional["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="task", cascade="all, delete-orphan", uselist=False
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("research_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    task: Mapped["ResearchTask"] = relationship("ResearchTask", back_populates="report")


class SavedStock(Base):
    __tablename__ = "saved_stocks"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_saved_stocks_user_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_stocks")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    market: Mapped[str] = mapped_column(String(50), nullable=False, default="NASDAQ")
    analysis_period: Mapped[str] = mapped_column(String(50), nullable=False, default="1 Year")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")


class StockOHLCV(Base):
    __tablename__ = "stock_ohlcv"
    __table_args__ = (
        UniqueConstraint("ticker", "interval", "timestamp", name="uq_stock_ohlcv_ticker_interval_timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    interval: Mapped[str] = mapped_column(String(20), nullable=False, default="1d")
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="Yahoo Finance")
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CompanyFinancialsProfile(Base):
    __tablename__ = "company_financials_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    financials_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    data_source: Mapped[str] = mapped_column(String(100), nullable=False, default="Yahoo Finance")
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DataRetrievalAuditLog(Base):
    __tablename__ = "data_retrieval_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data_source: Mapped[str] = mapped_column(String(100), nullable=False, default="Yahoo Finance")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


