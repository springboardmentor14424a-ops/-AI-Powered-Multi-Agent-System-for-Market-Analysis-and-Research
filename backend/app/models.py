from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

# Allowed values for ResearchTask.status
PENDING, PROCESSING, COMPLETED, FAILED = "pending", "processing", "completed", "failed"

# Primary-key columns are named user_id / task_id / saved_stock_id in the database
# (as in the module guide); in Python they are all just `.id`.


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Stored lowercase; the UNIQUE constraint is what really prevents duplicates.
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    # bcrypt hash only - the plain-text password is never stored.
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResearchTask(Base):
    """One stock-research request. Always belongs to exactly one user."""

    __tablename__ = "research_tasks"

    id: Mapped[int] = mapped_column("task_id", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis_period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PENDING, nullable=False)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SavedStock(Base):
    """A stock on a user's watchlist."""

    __tablename__ = "saved_stocks"
    __table_args__ = (
        # The same user can't save the same listing twice.
        UniqueConstraint("user_id", "market", "ticker", name="uq_saved_stock_user_market_ticker"),
    )

    id: Mapped[int] = mapped_column("saved_stock_id", Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserPreference(Base):
    """At most one row per user (user_id is the primary key)."""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    preferred_market: Mapped[str] = mapped_column(String(20), nullable=False)
    default_analysis_period: Mapped[str] = mapped_column(String(20), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
