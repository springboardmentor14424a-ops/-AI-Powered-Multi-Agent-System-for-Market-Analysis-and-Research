from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models
from app.schemas import UserRegister, UserResponse
from app.auth import hash_password,verify_password,create_access_token

from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import jwt, JWTError
from app.auth import SECRET_KEY, ALGORITHM

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Agent Stock Research Analyst",
    description="Backend API for stock research and user management",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to Multi-Agent Stock Research Analyst!",
        "status": "Backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/db-check")
def database_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"database": "PostgreSQL connected successfully!"}
    except Exception as e:
        return {"database": "Connection failed", "error": str(e)}


@app.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserRegister, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    existing_user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not existing_user or not verify_password(
        form_data.password, existing_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(existing_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    current_user = db.query(models.User).filter(
        models.User.id == int(user_id)
    ).first()

    if current_user is None:
        raise credentials_exception

    return current_user
@app.get("/users/me", response_model=UserResponse)
def read_current_user(
    current_user: models.User = Depends(get_current_user)
):
    return current_user