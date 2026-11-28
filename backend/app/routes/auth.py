from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse,
)
from app.services.user_service import register_user, login_user
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# -------------------------
# Registration API
# -------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    try:
        new_user = register_user(data, db)
        return new_user

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# -------------------------
# Login API
# -------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    try:
        access_token = login_user(
            email=str(data.email),
            password=data.password,
            db=db
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )


# -------------------------
# Protected Current User API
# -------------------------
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user