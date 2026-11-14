
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserResponse

from datetime import datetime, timedelta, timezone
import jwt

from app.core.config import settings
from app.schemas.auth import UserLogin

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.schemas.auth import GoogleLogin


router = APIRouter()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    email = user_data.email.strip().lower()

    # Check whether the email already exists
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    # Hash password using bcrypt
    password_bytes = user_data.password.encode("utf-8")

    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    # Create new user
    new_user = User(
        full_name=user_data.full_name.strip(),
        email=email,
        password_hash=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    return UserResponse(
        user_id=str(new_user.user_id),
        full_name=new_user.full_name,
        email=new_user.email
    )


@router.post("/login")
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    email = login_data.email.strip().lower()

    user = db.query(User).filter(
        User.email == email
    ).first()

    # Check user and password
    if not user or not bcrypt.checkpw(
        login_data.password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT token
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.user_id),
        "exp": expire
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "full_name": user.full_name,
            "email": user.email
        }
    }


@router.post("/google")
def google_login(
    login_data: GoogleLogin,
    db: Session = Depends(get_db)
):
    # Step 1: Verify the ID token with Google
    try:
        google_user = google_id_token.verify_oauth2_token(
            login_data.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google ID token"
        )

    # Step 2: Ensure Google has verified the email
    if google_user.get("email_verified") is not True:
        raise HTTPException(
            status_code=401,
            detail="Google email is not verified"
        )

    email = google_user.get("email", "").strip().lower()

    if not email:
        raise HTTPException(
            status_code=401,
            detail="Google account email not found"
        )

    # Step 3: Find an existing user
    user = db.query(User).filter(
        User.email == email
    ).first()

    # Step 4: Create a user if this is their first login
    if user is None:
        full_name = (
            google_user.get("name")
            or email.split("@")[0]
        )

        user = User(
            full_name=full_name[:150],
            email=email,
            password_hash=None
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)

        except IntegrityError:
            db.rollback()

            user = db.query(User).filter(
                User.email == email
            ).first()

            if user is None:
                raise HTTPException(
                    status_code=500,
                    detail="Unable to create Google account"
                )

    # Step 5: Generate StockIntel JWT
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.user_id),
        "exp": expire
    }

    access_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    # Step 6: Return the same authentication format
    return {
        "message": "Google login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "full_name": user.full_name,
            "email": user.email
        }
    }


