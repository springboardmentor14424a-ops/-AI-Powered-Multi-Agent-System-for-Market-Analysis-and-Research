from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
import models
from security import hash_password, verify_password, create_access_token, verify_token

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

@app.get("/")
def home():
    return {"message": "Welcome to Multi-Agent Stock Research Analyst API!"}

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

@app.post("/register")
def register_user(user: RegisterRequest, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = models.User(full_name=user.full_name, email=str(user.email), password_hash=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully!",
        "user_id": new_user.user_id,
        "full_name": new_user.full_name,
        "email": new_user.email
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
def login_user(user_credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": str(user.user_id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful!",
        "user": {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email
        }
    }

@app.get("/dashboard")
def get_dashboard(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    """
    This endpoint is protected. FastAPI will automatically check for a valid JWT.
    If the token is valid, it retrieves the specific user's data.
    """
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    return {
        "message": f"Welcome to your secure dashboard, {user.full_name}!",
        "user_id": user.user_id,
        "email": user.email,
        "status": "Authentication verified successfully"
    }

# --- WATCHLIST SCHEMAS & ENDPOINTS ---

class WatchlistCreate(BaseModel):
    stock_symbol: str

@app.post("/watchlist")
def add_to_watchlist(item: WatchlistCreate, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # 1. Verify the user exists
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Save the stock symbol to the database (convert to uppercase automatically)
    new_item = models.Watchlist(user_id=user.user_id, stock_symbol=item.stock_symbol.upper())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {
        "message": f"Successfully added {new_item.stock_symbol} to your watchlist!",
        "item": {
            "id": new_item.id,
            "stock_symbol": new_item.stock_symbol
        }
    }

@app.get("/watchlist")
def get_watchlist(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # Retrieve all stocks matching this user's ID
    watchlist = db.query(models.Watchlist).filter(models.Watchlist.user_id == user_id).all()
    
    return {
        "watchlist": [
            {
                "id": item.id, 
                "stock_symbol": item.stock_symbol, 
                "added_at": item.added_at
            } 
            for item in watchlist
        ]
    }