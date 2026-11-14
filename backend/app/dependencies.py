from datetime import datetime, timezone, timedelta
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings, SERVER_BOOT_TIME
from app.security import decode_access_token
from app.models import User, UserSession

security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    # 1. Check explicit Authorization Bearer header first (API client / programmatic requests)
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    # 2. Secondary: Extract session token from secure HTTP-only cookie (Browser requests)
    if not token:
        token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Retrieve server-side session from PostgreSQL database
    session = db.query(UserSession).filter(UserSession.session_id == token).first()

    # If token is a JWT containing session_id or user_id
    if not session:
        payload = decode_access_token(token)
        if payload:
            if "session_id" in payload:
                session = db.query(UserSession).filter(UserSession.session_id == payload["session_id"]).first()
            elif "sub" in payload:
                session = db.query(UserSession).filter(
                    UserSession.user_id == payload["sub"],
                    UserSession.is_active == True
                ).order_by(UserSession.last_activity.desc()).first()

    if not session or not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was invalidated. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now()

    # 4. Requirement 1 (System Restart Check):
    # Invalidate sessions created before current server process startup
    created_at = session.created_at
    if created_at.tzinfo is not None:
        created_at = created_at.astimezone().replace(tzinfo=None)
    if created_at < SERVER_BOOT_TIME:
        session.is_active = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired after system restart. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Requirement 3 & 4 (15-Minute Inactivity Timeout Check):
    last_act = session.last_activity
    if last_act.tzinfo is not None:
        last_act = last_act.astimezone().replace(tzinfo=None)
    idle_seconds = (now - last_act).total_seconds()
    max_idle_seconds = settings.SESSION_INACTIVITY_MINUTES * 60

    if idle_seconds > max_idle_seconds:
        session.is_active = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to inactivity. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 6. Reset inactivity sliding timer on user interaction
    session.last_activity = now
    session.expires_at = now + timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES)
    db.commit()

    user = session.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with session no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
