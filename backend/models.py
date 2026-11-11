from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    """The Users table: one row per registered person."""
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # never the real password
    preferred_market: Mapped[str] = mapped_column(String(10), default="NSE")
    default_period: Mapped[str] = mapped_column(String(5), default="1Y")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SavedStock(Base):
    """The user's watchlist."""
    __tablename__ = "saved_stocks"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),)

    saved_stock_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ResearchTask(Base):
    """Research history (filled in by later modules)."""
    __tablename__ = "research_tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(10))
    requested_period: Mapped[str] = mapped_column(String(5))
    status: Mapped[str] = mapped_column(String(20), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
