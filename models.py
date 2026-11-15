from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_tasks = relationship("ResearchTask", back_populates="owner")
    saved_stocks = relationship("SavedStock", back_populates="owner")

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    market = Column(String)
    requested_period = Column(String)
    status = Column(String, default="Pending") # Pending, Processing, Completed, Failed[cite: 5]
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Key linking task to the user[cite: 8]
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="research_tasks")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Key linking watchlist item to the user[cite: 8]
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="saved_stocks")

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    market = Column(String, default="NASDAQ")
    added_at = Column(DateTime, default=datetime.utcnow)

    # Optional relationship back to User if you have one configured
    user = relationship("User", backref="watchlist_items")

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    default_market = Column(String, default="NASDAQ")
    default_period = Column(String, default="1y")

    user = relationship("User", backref="preferences")