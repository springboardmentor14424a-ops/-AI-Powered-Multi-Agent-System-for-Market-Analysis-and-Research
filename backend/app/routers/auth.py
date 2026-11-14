from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, LoginOut, RegisterIn, RegisterOut, SessionOut, UserOut
from ..security import DUMMY_HASH, hash_password, verify_password
from ..session import cookie_args, start_session

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_TAKEN = "This email is already registered. Try signing in instead."
BAD_CREDENTIALS = "Incorrect email or password."


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
    # Accounts created through social sign-in have no password, so they can never match here.
    has_password = user is not None and user.password_hash is not None
    password_ok = verify_password(
        payload.password, user.password_hash if has_password else DUMMY_HASH
    )
    if not has_password or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, BAD_CREDENTIALS)

    csrf = start_session(response, user.id)

    return LoginOut(
        message="Signed in successfully.",
        user=UserOut.model_validate(user),
        csrf_token=csrf,
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME, **cookie_args())
    response.delete_cookie(settings.CSRF_COOKIE_NAME, **cookie_args())
    return {"message": "Signed out."}


@router.get("/me", response_model=SessionOut)
def me(request: Request, user: User = Depends(get_current_user)):
    """Lets the frontend restore the session after a page reload."""
    return SessionOut(
        user=UserOut.model_validate(user),
        csrf_token=request.cookies.get(settings.CSRF_COOKIE_NAME),
    )
