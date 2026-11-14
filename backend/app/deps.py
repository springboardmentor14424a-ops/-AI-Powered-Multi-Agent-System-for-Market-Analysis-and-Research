import secrets

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .security import decode_access_token

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
NOT_AUTHENTICATED = "Not authenticated. Please sign in again."


def verify_csrf(request: Request) -> None:
    """Double-submit check: the X-CSRF-Token header must match the csrf cookie."""
    cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header = request.headers.get(settings.CSRF_HEADER_NAME)
    if not cookie or not header or not secrets.compare_digest(
        cookie.encode(), header.encode()
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF validation failed.")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Authenticate via the HTTP-only cookie, or an Authorization: Bearer header."""
    token = request.cookies.get(settings.COOKIE_NAME)
    via_cookie = token is not None

    if token is None:
        scheme, _, credentials = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() == "bearer" and credentials:
            token = credentials.strip()

    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, NOT_AUTHENTICATED)

    # Browsers attach cookies automatically, so cookie-authenticated
    # state-changing requests must also prove they came from our frontend.
    if via_cookie and request.method not in SAFE_METHODS:
        verify_csrf(request)

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, NOT_AUTHENTICATED)

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, NOT_AUTHENTICATED)
    return user
