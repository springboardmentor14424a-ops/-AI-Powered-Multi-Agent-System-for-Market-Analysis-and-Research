from fundamental_agent import run_fundamental_analysis
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import yfinance as yf

from database import get_db
import models
import market_data
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

# --- DASHBOARD & PREFERENCES ENDPOINTS ---

@app.get("/dashboard")
def get_dashboard(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    
    return {
        "message": f"Welcome to your secure dashboard, {user.full_name}!",
        "user_id": user.user_id,
        "email": user.email,
        "preferred_market": user.preferred_market or "NASDAQ",
        "preferred_period": user.preferred_period or "1 Year",
        "status": "Authentication verified successfully"
    }

class PreferencesUpdate(BaseModel):
    preferred_market: str
    preferred_period: str

@app.put("/preferences")
def update_preferences(prefs: PreferencesUpdate, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.preferred_market = prefs.preferred_market
    user.preferred_period = prefs.preferred_period
    db.commit()
    
    return {
        "message": "Preferences updated successfully",
        "preferred_market": user.preferred_market,
        "preferred_period": user.preferred_period
    }

# --- WATCHLIST SCHEMAS & ENDPOINTS ---

class WatchlistCreate(BaseModel):
    stock_symbol: str

@app.post("/watchlist")
def add_to_watchlist(item: WatchlistCreate, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
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

@app.delete("/watchlist/{item_id}")
def remove_from_watchlist(item_id: int, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    item = db.query(models.Watchlist).filter(
        models.Watchlist.id == item_id, 
        models.Watchlist.user_id == user_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in your watchlist")
        
    db.delete(item)
    db.commit()
    
    return {"message": f"Successfully removed {item.stock_symbol} from watchlist"}

# --- YAHOO FINANCE ENDPOINT ---

@app.get("/stock/{symbol}")
def get_stock_data(symbol: str, user_id: int = Depends(verify_token)):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"Could not find market data for {symbol}")
            
        current_price = hist['Close'].iloc[-1]
        
        info = ticker.info
        company_name = info.get("shortName", symbol)
        currency = info.get("currency", "USD")
        
        return {
            "symbol": symbol.upper(),
            "company_name": company_name,
            "current_price": round(current_price, 2),
            "currency": currency
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching data from Yahoo Finance: {str(e)}")

# --- RESEARCH HISTORY ENDPOINTS ---

class ResearchCreate(BaseModel):
    ticker: str

@app.post("/research/start")
def start_research_task(request: ResearchCreate, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_task = models.ResearchTask(
        user_id=user.user_id,
        ticker=request.ticker.upper(),
        market=user.preferred_market or "NASDAQ",
        requested_period=user.preferred_period or "1 Year",
        status="Pending"
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return {
        "message": f"Research task started for {new_task.ticker}",
        "task": {
            "task_id": new_task.task_id,
            "ticker": new_task.ticker,
            "status": new_task.status
        }
    }

@app.get("/research/history")
def get_research_history(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    tasks = db.query(models.ResearchTask).filter(
        models.ResearchTask.user_id == user_id
    ).order_by(models.ResearchTask.created_at.desc()).all()
    
    return {
        "history": [
            {
                "task_id": task.task_id,
                "ticker": task.ticker,
                "market": task.market,
                "requested_period": task.requested_period,
                "status": task.status,
                "created_at": task.created_at
            }
            for task in tasks
        ]
    }

# --- MODULE 2: STOCK SEARCH & MARKET DATA ENDPOINTS ---

@app.get("/stocks/search")
def search_stock(query: str, user_id: int = Depends(verify_token)):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    return market_data.search_companies(query)

@app.get("/stocks/data/{symbol}")
def get_market_data(
    symbol: str,
    market: Optional[str] = None,
    period: Optional[str] = None,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    selected_market = market or (user.preferred_market if user else "NASDAQ") or "NASDAQ"
    selected_period = period or (user.preferred_period if user else "1 Year") or "1 Year"

    try:
        data = market_data.get_full_market_data(
            symbol=symbol,
            market=selected_market,
            period=selected_period
        )
        if not data["validation"]["is_valid"]:
            raise HTTPException(
                status_code=404,
                detail=f"No valid market data found for {symbol} on {selected_market}"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve market data: {str(e)}")

# --- MODULE 3: FUNDAMENTAL ANALYSIS AGENT ENDPOINT ---

@app.get("/agents/fundamental/{symbol}")
def get_fundamental_analysis(
    symbol: str,
    market: Optional[str] = None,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    selected_market = market or (user.preferred_market if user else "NASDAQ") or "NASDAQ"

    try:
        return run_fundamental_analysis(symbol=symbol, market=selected_market)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fundamental analysis failed: {str(e)}")