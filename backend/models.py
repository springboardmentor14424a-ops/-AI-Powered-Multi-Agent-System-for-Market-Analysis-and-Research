from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class AgentResult(Base):
    """What each research agent produced (used by the agents in later points)."""
    __tablename__ = "agent_results"

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.task_id", ondelete="CASCADE"), index=True)
    agent_name: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20))
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SourceDocument(Base):
    """Where every piece of data came from, and when it was retrieved."""
    __tablename__ = "source_documents"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ResearchReport(Base):
    """The final combined report (filled in by a later point)."""
    __tablename__ = "research_reports"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True, index=True
    )
    report_content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


from sqlalchemy import BigInteger, Date, Float


class StaticCompany(Base):
    """Company profile from the Kaggle NIFTY-50 dataset (static data)."""
    __tablename__ = "static_companies"

    company_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True)


class StaticPrice(Base):
    """Cleaned daily prices (OHLCV) from the Kaggle NIFTY-50 dataset (static data)."""
    __tablename__ = "static_prices"
    __table_args__ = (UniqueConstraint("symbol", "trade_date", name="uq_static_symbol_date"),)

    price_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    trade_date: Mapped[datetime] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(200))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    