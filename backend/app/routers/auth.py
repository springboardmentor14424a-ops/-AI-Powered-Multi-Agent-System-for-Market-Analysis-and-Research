from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, LoginOut, RegisterIn, RegisterOut, SessionOut, UserOut
from ..security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    new_csrf_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_TAKEN = "This email is already registered. Try signing in instead."
BAD_CREDENTIALS = "Incorrect email or password."


def _cookie_args() -> dict:
    return {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }


@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_TAKEN)

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous sign-ups with the same email
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_TAKEN)

    return RegisterOut(
        message="Registration successful! You can now sign in.",
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    # Always run one bcrypt verification so timing doesn't reveal whether the
    # email exists, and use one generic message for both failure cases.
    password_ok = verify_password(
        payload.password, user.password_hash if user else DUMMY_HASH
    )
    if user is None or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, BAD_CREDENTIALS)

    token = create_access_token(user.id)
    csrf = new_csrf_token()
    max_age = settings.JWT_EXPIRE_MINUTES * 60
    response.set_cookie(settings.COOKIE_NAME, token, max_age=max_age, **_cookie_args())
    response.set_cookie(settings.CSRF_COOKIE_NAME, csrf, max_age=max_age, **_cookie_args())

    return LoginOut(
        message="Signed in successfully.",
        user=UserOut.model_validate(user),
        csrf_token=csrf,
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME, **_cookie_args())
    response.delete_cookie(settings.CSRF_COOKIE_NAME, **_cookie_args())
    return {"message": "Signed out."}


@router.get("/me", response_model=SessionOut)
def me(request: Request, user: User = Depends(get_current_user)):
    """Lets the frontend restore the session after a page reload."""
    return SessionOut(
        user=UserOut.model_validate(user),
        csrf_token=request.cookies.get(settings.CSRF_COOKIE_NAME),
    )
