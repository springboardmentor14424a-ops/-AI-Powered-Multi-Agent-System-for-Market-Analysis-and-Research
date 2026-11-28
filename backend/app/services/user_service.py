from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import hash_password, verify_password, create_access_token


# -------------------------
# User Registration Service
# -------------------------
def register_user(user_data: UserRegister, db: Session):

    # 1. Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == str(user_data.email)
    ).first()

    if existing_user:
        raise ValueError("Email already registered")

    # 2. Hash password
    hashed_password = hash_password(user_data.password)

    # 3. Create new user
    new_user = User(
        full_name=user_data.full_name,
        email=str(user_data.email),
        password_hash=hashed_password
    )

    # 4. Save to database
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    # 5. Return created user
    return new_user


# -------------------------
# User Login Service
# -------------------------
def login_user(email: str, password: str, db: Session):

    # 1. Find user using email
    user = db.query(User).filter(
        User.email == email
    ).first()

    # 2. Check if user exists
    if not user:
        raise ValueError("Invalid email or password")

    # 3. Verify password
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    # 4. Generate JWT token using user ID
    access_token = create_access_token(
        subject=str(user.user_id)
    )

    # 5. Return token
    return access_token