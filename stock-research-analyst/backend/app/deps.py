import secrets

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_access_token

ACCESS_COOKIE = "access_token"
CSRF_COOKIE = "csrf_token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated or session expired. Please sign in again.",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Identify the caller from the verified JWT. The user id NEVER comes from the client."""
    token = request.cookies.get(ACCESS_COOKIE)
    from_cookie = token is not None
    if not token:
        scheme, _, credentials = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() == "bearer" and credentials:
            token = credentials
    if not token:
        raise _unauthorized()

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise _unauthorized()

    # CSRF protection for cookie-authenticated state-changing requests
    # (signed double-submit: header must match the csrf claim inside the JWT).
    if from_cookie and request.method in UNSAFE_METHODS:
        header = request.headers.get("X-CSRF-Token", "")
        if not secrets.compare_digest(header.encode(), str(payload.get("csrf", "")).encode()):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid or missing CSRF token.")

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user
