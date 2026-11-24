
import secrets

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db, settings
from app.models import User
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse
)

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    validate_csrf
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# --------------------------------------------------
# AUTHENTICATION COOKIE CREATION
# --------------------------------------------------

def set_auth_cookies(response: Response, user_id: int):

    token = create_access_token(user_id)
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )


# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).strip().lower()

    full_name = data.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name cannot be empty"
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(data.password)
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:

        db.rollback()

        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered"
            )

        raise

    return {
        "message": "Registration successful",
        "user_id": user.user_id
    }


# --------------------------------------------------
# USER LOGIN
# --------------------------------------------------

@router.post("/login")
def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):

    email = str(data.email).strip().lower()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    set_auth_cookies(response, user.user_id)

    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user)
    }


# --------------------------------------------------
# GET CURRENT LOGGED-IN USER
# --------------------------------------------------

@router.get("/me", response_model=UserResponse)
def get_me(
    user: User = Depends(get_current_user)
):
    return user


# --------------------------------------------------
# USER LOGOUT
# --------------------------------------------------

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user)
):

    validate_csrf(request)

    response.delete_cookie(
        "access_token",
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite="lax"
    )

    response.delete_cookie(
        "csrf_token",
        path="/",
        secure=settings.COOKIE_SECURE,
        httponly=False,
        samesite="lax"
    )

    return {
        "message": "Logged out successfully"
    }
