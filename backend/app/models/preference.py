from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    risk_tolerance = Column(String(50), default="Moderate")
    preferred_market = Column(String(50), default="NSE")
    analysis_period = Column(String(50), default="1 Year")

    # Relationship back to User
    user = relationship("User", back_populates="preference")