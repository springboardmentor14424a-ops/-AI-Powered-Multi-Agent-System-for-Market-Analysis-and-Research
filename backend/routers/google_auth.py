from fastapi import APIRouter, Depends, HTTPException, Response, status
import httpx
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_handler import create_access_token
from database.connection import get_db
from models.user import User
from schemas.auth import GoogleLoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth/google", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate or register a user via Google ID token."""

    # Verify the Google ID token
    async with httpx.AsyncClient() as client:
        google_resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
        )

    if google_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        )

    token_info = google_resp.json()
    email: str = token_info.get("email", "")
    name: str = token_info.get("name", email.split("@")[0])
    sub: str = token_info.get("sub", "")

    if not email or not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract user info from Google token.",
        )

    # Look up user by google_id or email
    result = await db.execute(
        select(User).where(or_(User.google_id == sub, User.email == email))
    )
    user: User | None = result.scalar_one_or_none()

    if user:
        # Link google_id if not yet linked
        if not user.google_id:
            user.google_id = sub
            await db.flush()
            await db.refresh(user)
    else:
        # Create new user
        user = User(
            full_name=name,
            email=email,
            google_id=sub,
            password_hash=None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
