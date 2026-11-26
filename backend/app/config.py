from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/stock_research"
    jwt_secret_key: str = "replace-this-in-production"
    jwt_expire_minutes: int = 60
    frontend_origin: str = "http://localhost:5173"
    google_client_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
