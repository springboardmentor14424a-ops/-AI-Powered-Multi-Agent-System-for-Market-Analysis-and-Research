from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_handler import decode_token
from database.connection import get_db
from models.user import User

# Optional bearer – we fall back to cookie if header is absent
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract the JWT from the Authorization Bearer header or the 'access_token'
    cookie, decode it, and return the matching User row.

    Raises HTTP 401 if the token is missing, invalid, expired, or the user
    no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: Optional[str] = None

    # 1. Prefer the Authorization header
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # 2. Fall back to the cookie
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
