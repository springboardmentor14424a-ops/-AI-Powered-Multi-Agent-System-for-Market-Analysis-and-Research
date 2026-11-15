import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # e.g. password longer than bcrypt's 72-byte limit
        return False


# Used to keep login timing similar whether or not the email exists.
DUMMY_HASH = hash_password("not-a-real-password-1")


def create_access_token(user_id: int) -> tuple[str, str]:
    """Return (jwt, csrf_token). The token holds only the user id, expiry and a CSRF value."""
    now = datetime.now(timezone.utc)
    csrf = secrets.token_urlsafe(32)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "csrf": csrf,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM), csrf


def decode_access_token(token: str) -> dict:
    """Verifies signature and expiry; raises jwt.PyJWTError if invalid."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "sub"]},
    )
