
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
import models
from security import hash_password


# Create FastAPI application
app = FastAPI(title="Multi-Agent Stock Research Analyst")


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to Multi-Agent Stock Research Analyst API!"
    }


# Registration request model
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str


# Registration API
@app.post("/register")
def register_user(
    user: RegisterRequest,
    db: Session = Depends(get_db)
):

    # Check whether passwords match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    # Check whether email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create new user
    new_user = models.User(
        full_name=user.full_name,
        email=str(user.email),
        password_hash=hashed_password
    )

    # Save user in database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully!",
        "user_id": new_user.user_id,
        "full_name": new_user.full_name,
        "email": new_user.email
    }
