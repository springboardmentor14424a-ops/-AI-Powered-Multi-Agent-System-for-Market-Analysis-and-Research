import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# Verified against when the email is unknown, so "no such user" and "wrong
# password" take about the same time (prevents user enumeration by timing).
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: int) -> str:
    """JWT carrying only the user id and timestamps - no password or personal data."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id if the signature and expiry are valid, else None."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
