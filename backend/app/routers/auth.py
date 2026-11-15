from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import UserRegister, UserLogin, UserResponse, Token
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

router = APIRouter(prefix="", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    Validates incoming email/password, checks duplicate email, hashes password with bcrypt,
    and initializes default preferences.
    """
    clean_email = user_in.email.lower().strip()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Hash the password with bcrypt (never store plain password)
    hashed_pwd = hash_password(user_in.password)

    new_user = User(
        full_name=user_in.full_name.strip(),
        email=clean_email,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize default user preferences
    default_prefs = UserPreference(
        user_id=new_user.user_id,
        preferred_market="NSE",
        preferred_analysis_period="6 Months"
    )
    db.add(default_prefs)
    db.commit()

    return new_user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and issue a signed JWT containing user_id and expiry time.
    """
    clean_email = login_data.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    # Generate JWT containing user_id and expiry time
    access_token = create_access_token(user_id=user.user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently logged in user directly from JWT."""
    return current_user

