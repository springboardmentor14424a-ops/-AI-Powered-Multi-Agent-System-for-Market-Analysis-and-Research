from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError

from config import settings


def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict. Must contain 'sub' (user_id as string).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        jose.JWTError: If the token is invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    return payload
