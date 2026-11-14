import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/stock_analyst",
    )

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # bcrypt work factor (12 is a sensible default; tests lower it for speed)
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Datasets / market-data providers
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parents[1] / "data")))
    # SEC EDGAR requires a descriptive User-Agent with contact info, e.g. "Your Name you@example.com".
    # If empty, EDGAR is skipped and Yahoo Finance fundamentals are used instead.
    SEC_USER_AGENT: str = os.getenv("SEC_USER_AGENT", "").strip()
    HTTP_TIMEOUT: int = int(os.getenv("DATA_HTTP_TIMEOUT", "15"))

    # Social sign-in (all optional; a provider is enabled when its credentials are set).
    # PUBLIC_URL is the address users open in the browser (the frontend). Redirect URIs
    # registered with each provider are  PUBLIC_URL + /api/auth/oauth/<provider>/callback
    PUBLIC_URL: str = os.getenv("PUBLIC_URL", "http://localhost:5173").rstrip("/")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "").strip()
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "").strip()
    MICROSOFT_TENANT: str = os.getenv("MICROSOFT_TENANT", "common").strip() or "common"
    X_CLIENT_ID: str = os.getenv("X_CLIENT_ID", "").strip()
    X_CLIENT_SECRET: str = os.getenv("X_CLIENT_SECRET", "").strip()
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "").strip()  # the "Services ID"
    APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "").strip()
    APPLE_KEY_ID: str = os.getenv("APPLE_KEY_ID", "").strip()
    # The .p8 private key: either the PEM text (use \n for line breaks) or a file path.
    APPLE_PRIVATE_KEY: str = os.getenv("APPLE_PRIVATE_KEY", "").strip()
    APPLE_PRIVATE_KEY_PATH: str = os.getenv("APPLE_PRIVATE_KEY_PATH", "").strip()

    # Cookies
    COOKIE_NAME: str = "access_token"
    CSRF_COOKIE_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    # Secure=True means the browser only sends the cookie over HTTPS.
    # Set COOKIE_SECURE=false ONLY for local http development.
    COOKIE_SECURE: bool = _bool("COOKIE_SECURE", True)
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")

    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]


settings = Settings()

if len(settings.JWT_SECRET) < 32:
    raise RuntimeError(
        "JWT_SECRET must be set to a random string of at least 32 characters.\n"
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )
