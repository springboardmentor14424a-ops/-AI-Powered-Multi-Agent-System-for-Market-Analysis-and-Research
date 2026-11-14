import uuid
from datetime import datetime, timezone, timedelta
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference, UserSession
from app.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, GoogleAuthRequest
from app.security import hash_password, verify_password, create_access_token, generate_session_token
from app.config import settings
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegisterRequest, db: Session = Depends(get_db)):
    email_clean = user_in.email.lower().strip()

    # Check whether the email is already registered
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    # Hash the password using secure password-hashing algorithm (bcrypt)
    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        full_name=user_in.full_name.strip(),
        email=email_clean,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.flush()

    # Store default user preferences associated with the user
    default_prefs = UserPreference(
        user_id=new_user.user_id,
        preferred_market="NASDAQ",
        default_analysis_period="1 Year"
    )
    db.add(default_prefs)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    email_clean = login_in.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Invalidate any prior active sessions for this user on new manual login
    db.query(UserSession).filter(
        UserSession.user_id == user.user_id,
        UserSession.is_active == True
    ).update({"is_active": False})

    # Create new server-side session in PostgreSQL
    now = datetime.now()
    session_token = generate_session_token()
    new_session = UserSession(
        session_id=session_token,
        user_id=user.user_id,
        created_at=now,
        last_activity=now,
        expires_at=now + timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES),
        is_active=True
    )
    db.add(new_session)
    db.commit()

    # Set secure, HTTP-only, SameSite session cookie (no max_age/expires => cleared on browser close)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        path="/"
    )

    return TokenResponse(
        access_token=session_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/google", response_model=TokenResponse)
def continue_with_google(google_in: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate or automatically register a user via 'Continue with Google'.
    Accepts a Google credential (ID Token) or verified Google email and profile details.
    """
    email = None
    full_name = None

    # 1. If Google credential is provided, verify via Google tokeninfo or userinfo endpoint
    if google_in.credential:
        try:
            with httpx.Client(timeout=5.0) as client:
                # Check if it's an ID token
                res = client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={google_in.credential}")
                if res.status_code == 200:
                    info = res.json()
                    email = info.get("email")
                    full_name = info.get("name")
                else:
                    # Check if it's an access token
                    res2 = client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {google_in.credential}"}
                    )
                    if res2.status_code == 200:
                        info2 = res2.json()
                        email = info2.get("email")
                        full_name = info2.get("name")
        except Exception:
            pass

    # 2. Fall back to passed email and full_name
    if not email and google_in.email:
        email = str(google_in.email)
        full_name = google_in.full_name or email.split("@")[0].title()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid Google account email or token credential is required."
        )

    email_clean = email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    # 3. If user doesn't exist yet, auto-register them
    if not user:
        pwd_to_hash = google_in.password if google_in.password else str(uuid.uuid4())
        user = User(
            full_name=full_name or email_clean.split("@")[0].title(),
            email=email_clean,
            password_hash=hash_password(pwd_to_hash)
        )
        db.add(user)
        db.flush()

        default_prefs = UserPreference(
            user_id=user.user_id,
            preferred_market="NASDAQ",
            default_analysis_period="1 Year"
        )
        db.add(default_prefs)
        db.commit()
        db.refresh(user)

    # Invalidate previous active sessions on new Google login
    db.query(UserSession).filter(
        UserSession.user_id == user.user_id,
        UserSession.is_active == True
    ).update({"is_active": False})

    # 4. Create new server-side session in PostgreSQL
    now = datetime.now()
    session_token = generate_session_token()
    new_session = UserSession(
        session_id=session_token,
        user_id=user.user_id,
        created_at=now,
        last_activity=now,
        expires_at=now + timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES),
        is_active=True
    )
    db.add(new_session)
    db.commit()

    # Set secure, HTTP-only, SameSite session cookie (no max_age/expires => cleared on browser close)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        path="/"
    )

    return TokenResponse(
        access_token=session_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Invalidate current server-side session and remove authentication cookie.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if token:
        session = db.query(UserSession).filter(UserSession.session_id == token).first()
        if session:
            session.is_active = False
            db.commit()

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax"
    )
    return {"status": "ok", "message": "Session invalidated successfully."}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
