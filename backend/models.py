from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # NEW: User Preferences
    preferred_market = Column(String(50), server_default="NASDAQ")
    preferred_period = Column(String(50), server_default="1 Year")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    # This securely links the saved stock to the specific user's ID
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    stock_symbol = Column(String, index=True, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
class ResearchTask(Base):
    __tablename__ = "research_tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    ticker = Column(String, index=True, nullable=False)
    market = Column(String, nullable=False)
    requested_period = Column(String, nullable=False)
    status = Column(String, default="Pending") # Pending, Processing, Completed, or Failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)    