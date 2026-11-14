import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = str(BASE_DIR / ".env")

# Record server boot timestamp to invalidate sessions from before server/system restart
SERVER_BOOT_TIME = datetime.now()
SERVER_INSTANCE_ID = secrets.token_hex(16)

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./stock_research.db"
    SECRET_KEY: str = "9a8d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    SESSION_INACTIVITY_MINUTES: int = 15     # 15 minutes inactivity timeout
    SESSION_COOKIE_NAME: str = "session_token"
    SESSION_COOKIE_SECURE: bool = False      # False on localhost HTTP
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

settings = Settings()
