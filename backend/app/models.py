import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def local_now():
    return datetime.now()

def utc_now():
    return datetime.now()

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_market = Column(String(20), default="NASDAQ", nullable=False)  # NSE, BSE, NASDAQ, NYSE
    default_analysis_period = Column(String(20), default="1 Year", nullable=False)  # 1 Month, 3 Months, 6 Months, 1 Year, 5 Years
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="preferences")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=True)
    market = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )

    user = relationship("User", back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), nullable=False)
    company_name = Column(String(255), nullable=True)
    market = Column(String(20), nullable=False)
    requested_period = Column(String(20), nullable=False)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Processing, Completed, Failed
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="research_tasks")
    report = relationship("ResearchReport", back_populates="task", uselist=False, cascade="all, delete-orphan")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    task_id = Column(String(36), ForeignKey("research_tasks.task_id", ondelete="CASCADE"), unique=True, nullable=False)
    report_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("ResearchTask", back_populates="report")


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_activity = Column(DateTime, default=utc_now, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="sessions")

