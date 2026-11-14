import os

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import RegisterSchema, LoginSchema, UserResponse
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)

class GoogleLoginSchema(BaseModel):
    credential: str

router = APIRouter(prefix="/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer(auto_error=False)


# USER REGISTRATION
@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: RegisterSchema,
    db: Session = Depends(get_db)
):

    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    email = user_data.email.strip().lower()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    new_user = User(
        full_name=user_data.full_name.strip(),
        email=email,
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# USER LOGIN
@router.post("/login")
def login_user(
    user_data: LoginSchema,
    db: Session = Depends(get_db)
):

    email = user_data.email.strip().lower()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if (
    not user
    or not user.password_hash
    or not verify_password(
        user_data.password,
        user.password_hash
    )
    ):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

    token = create_access_token(user.user_id)

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email
        }
    }

@router.post("/google")
def google_login(
    data: GoogleLoginSchema,
    db: Session = Depends(get_db)
):
    try:
        google_user = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )

        google_sub = google_user["sub"]
        email = google_user["email"]
        full_name = google_user.get("name", "Google User")

        if not google_user.get("email_verified", False):
            raise HTTPException(
                status_code=401,
                detail="Google email is not verified"
            )

        email = email.strip().lower()

        user = db.query(User).filter(
            User.google_sub == google_sub
        ).first()

        if not user:
            user = db.query(User).filter(
                User.email == email
            ).first()

            if user:
                # Link Google to an existing account only
                # after verifying the same email.
                if user.google_sub and user.google_sub != google_sub:
                    raise HTTPException(
                        status_code=409,
                        detail="This email is linked to another Google account"
                    )

                user.google_sub = google_sub

            else:
                user = User(
                    full_name=full_name,
                    email=email,
                    google_sub=google_sub,
                    password_hash=None
                )

                db.add(user)

            db.commit()
            db.refresh(user)

        token = create_access_token(user.user_id)

        return {
            "message": "Google login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google authentication"
        )
    
# AUTHENTICATION DEPENDENCY
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# PROTECTED USER PROFILE
@router.get("/me", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):

    return current_user