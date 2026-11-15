from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str  # required: the app refuses to start without it
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_SECURE: bool = False
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    RESEARCH_STUB_DELAY_SECONDS: float = 3
    # Use Yahoo Finance (via yfinance) for stock search; falls back to the built-in list on any failure.
    YAHOO_SEARCH_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
