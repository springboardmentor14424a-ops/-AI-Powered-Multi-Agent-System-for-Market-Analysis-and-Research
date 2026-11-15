import pathlib
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

_env_file_path = pathlib.Path(__file__).parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stock_research"
    SECRET_KEY: str = "ansduciewohfcfosidcndslkvnhwdufhewofpfj"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_CLIENT_ID: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
