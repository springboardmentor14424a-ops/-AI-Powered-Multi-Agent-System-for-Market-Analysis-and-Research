
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.sql import func

from app.database.database import Base


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    saved_stock_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    ticker = Column(
        String(30),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Prevent the same user from saving a ticker twice
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            name="uq_user_saved_stock"
        ),
    )
