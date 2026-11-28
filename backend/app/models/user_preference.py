
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


class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    preferred_market = Column(
        String(20),
        nullable=False,
        default="NSE"
    )

    default_analysis_period = Column(
        String(20),
        nullable=False,
        default="1y"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_user_preference"
        ),
    )
