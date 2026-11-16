from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class SavedStock(Base):
    __tablename__ = "saved_stocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(20), index=True, nullable=False)     # e.g., INFY, RELIANCE, AAPL
    company_name = Column(String(150), nullable=True)
    exchange = Column(String(20), default="NSE")
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saved_stocks")