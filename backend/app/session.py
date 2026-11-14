"""Starting and ending a login session (shared by password login and social sign-in)."""
from fastapi import Response

from .config import settings
from .security import create_access_token, new_csrf_token


def cookie_args() -> dict:
    return {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }


def start_session(response: Response, user_id: int) -> str:
    """Set the JWT cookie (HTTP-only) and the CSRF cookie. Returns the CSRF token."""
    csrf = new_csrf_token()
    max_age = settings.JWT_EXPIRE_MINUTES * 60
    response.set_cookie(settings.COOKIE_NAME, create_access_token(user_id), max_age=max_age, **cookie_args())
    response.set_cookie(settings.CSRF_COOKIE_NAME, csrf, max_age=max_age, **cookie_args())
    return csrf
