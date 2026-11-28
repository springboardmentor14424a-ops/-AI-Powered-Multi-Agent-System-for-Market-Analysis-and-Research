from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Locate backend/.env reliably
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Agent Stock Research Analyst"

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "stock_research_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


settings = Settings()