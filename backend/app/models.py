import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, Index, Float
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    research_tasks = relationship("ResearchTask", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Enforce uniqueness per user to prevent duplicate ticker entries for the same user
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_user_ticker"),
    )

    user = relationship("User", back_populates="saved_stocks")


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    company_name = Column(String(120), nullable=True)
    market = Column(String(20), nullable=False, default="NSE")
    requested_period = Column(String(30), nullable=False, default="6 Months")
    status = Column(String(20), nullable=False, default="Pending")  # Pending, Processing, Completed, Failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Research report outputs
    summary = Column(Text, nullable=True)
    recommendation = Column(String(20), nullable=True)  # Strong Buy, Buy, Hold, Sell
    target_price = Column(String(50), nullable=True)
    report_json = Column(Text, nullable=True)

    user = relationship("User", back_populates="research_tasks")
    report = relationship("ResearchReport", back_populates="task", uselist=False, cascade="all, delete-orphan")
    agent_results = relationship("AgentResult", back_populates="task", cascade="all, delete-orphan")
    source_documents = relationship("SourceDocument", back_populates="task", cascade="all, delete-orphan")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    report_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    consolidated_report = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    limitations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    task = relationship("ResearchTask", back_populates="report")


class AgentResult(Base):
    __tablename__ = "agent_results"

    result_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="Completed")
    structured_output = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    task = relationship("ResearchTask", back_populates="agent_results")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("research_tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    source_title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    publication_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    retrieval_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    task = relationship("ResearchTask", back_populates="source_documents")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    preferred_market = Column(String(20), nullable=False, default="NSE")
    preferred_analysis_period = Column(String(30), nullable=False, default="6 Months")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="preferences")


class MarketDataRecord(Base):
    __tablename__ = "market_data_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(20), nullable=False, default="NSE", index=True)
    record_date = Column(String(30), nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "market", "record_date", name="uq_ticker_market_date"),
    )


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    profile_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(20), nullable=False, default="NSE", index=True)
    company_name = Column(String(150), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    ceo = Column(String(100), nullable=True)
    employees = Column(Integer, nullable=True)
    headquarters = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    market_cap = Column(String(50), nullable=True)
    pe_ratio = Column(Float, nullable=True)
    week_52_high = Column(Float, nullable=True)
    week_52_low = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "market", name="uq_profile_ticker_market"),
    )


class CompanyFinancial(Base):
    __tablename__ = "company_financials"

    financial_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(20), nullable=False, default="NSE", index=True)
    period_type = Column(String(20), nullable=False, default="annual")  # annual, quarterly
    statement_type = Column(String(50), nullable=False, default="all")  # income_statement, balance_sheet, cash_flow, all
    data_json = Column(Text, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    data_source = Column(String(100), nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "market", "period_type", "statement_type", name="uq_financial_ticker_period"),
    )


class DataValidationLog(Base):
    __tablename__ = "data_validation_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(20), nullable=False, default="NSE")
    total_records = Column(Integer, nullable=False)
    clean_records = Column(Integer, nullable=False)
    missing_values_handled = Column(Integer, nullable=False, default=0)
    duplicate_dates_removed = Column(Integer, nullable=False, default=0)
    inconsistencies_corrected = Column(Integer, nullable=False, default=0)
    quality_score = Column(Float, nullable=False, default=100.0)
    is_valid = Column(String(10), nullable=False, default="true")
    issues_json = Column(Text, nullable=True)
    data_source = Column(String(100), nullable=False)
    validated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


