
import uuid

from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=True)

    # User preferences
    preferred_market = Column(
        String(20), nullable=False, default="NSE", server_default="NSE"
    )

    preferred_analysis_period = Column(
        String(20), nullable=False, default="1y", server_default="1y"
    )

    preferred_indicators = Column(
        JSONB,
        nullable=False,
        default=lambda: ["SMA", "EMA", "RSI", "MACD"],
        server_default='["SMA","EMA","RSI","MACD"]'
    )

    preferred_news_window = Column(
        String(20), nullable=False, default="30 days",
        server_default="30 days"
    )

    preferred_risk_view = Column(
        String(20), nullable=False, default="Balanced",
        server_default="Balanced"
    )

    preferred_report_format = Column(
        String(20), nullable=False, default="Markdown",
        server_default="Markdown"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
