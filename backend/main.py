from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import datetime
import yfinance as yf

import database
import models
import schemas
import auth

# Initialize structural database models locally on startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Multi-Agent Stock Analyst - Module 1 Core Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock down origins specifically to your React server port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. USER REGISTRATION & LOGIN SYSTEM ---

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserRegister, db: Session = Depends(database.get_db)):
    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
        
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    hashed_pwd = auth.hash_password(user_data.password)
    new_user = models.User(full_name=user_data.full_name, email=user_data.email, password_hash=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize workspace preference block defaults instantly
    pref = models.UserPreference(user_id=new_user.user_id)
    db.add(pref)
    db.commit()
    
    return {"message": "User registered successfully."}

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
        
    token = auth.create_access_token(data={"user_id": user.user_id})
    return {"access_token": token, "token_type": "bearer"}

# --- 2. PERSONALIZED PREFERENCES & HISTORY WORKSPACE ---

@app.get("/api/workspace/preferences")
def get_preferences(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    prefs = db.query(models.UserPreference).filter(models.UserPreference.user_id == current_user.user_id).first()
    return prefs

@app.put("/api/workspace/preferences")
def update_preferences(pref_data: schemas.PreferenceUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    prefs = db.query(models.UserPreference).filter(models.UserPreference.user_id == current_user.user_id).first()
    prefs.preferred_market = pref_data.preferred_market.upper()
    prefs.default_period = pref_data.default_period
    db.commit()
    return {"message": "Preferences updated successfully."}

@app.get("/api/workspace/history")
def get_research_history(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Deriving user identity securely from token payload parameters
    history = db.query(models.ResearchTask).filter(models.ResearchTask.user_id == current_user.user_id).all()
    return history

# --- 3. WATCHLIST OPERATIONAL INTERFACES ---

@app.get("/api/watchlist")
def get_watchlist(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    stocks = db.query(models.SavedStock).filter(models.SavedStock.user_id == current_user.user_id).all()
    return stocks

@app.post("/api/watchlist")
def add_to_watchlist(stock: schemas.WatchlistAdd, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    ticker_clean = stock.ticker.strip().upper()
    duplicate = db.query(models.SavedStock).filter(
        models.SavedStock.user_id == current_user.user_id, 
        models.SavedStock.ticker == ticker_clean
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Stock already saved to your watchlist.")
        
    new_stock = models.SavedStock(user_id=current_user.user_id, ticker=ticker_clean)
    db.add(new_stock)
    db.commit()
    return {"message": f"{ticker_clean} added to watchlist successfully."}

@app.delete("/api/watchlist/{ticker}")
def remove_from_watchlist(ticker: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    stock_item = db.query(models.SavedStock).filter(
        models.SavedStock.user_id == current_user.user_id,
        models.SavedStock.ticker == ticker.upper()
    ).first()
    if not stock_item:
        raise HTTPException(status_code=404, detail="Stock not found in your watchlist.")
    db.delete(stock_item)
    db.commit()
    return {"message": "Stock removed from watchlist successfully."}

# --- 4. STOCK DATA RETRIEVAL PIPELINE (MILESTONE 1 INTEGRATION) ---

@app.get("/api/market/search")
def search_stock(ticker: str, market: str = "NSE", period: str = "1y", current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    ticker_clean = ticker.strip().upper()
    
    # Track task creation dynamically within logs
    task = models.ResearchTask(
        user_id=current_user.user_id, ticker=ticker_clean, market=market, requested_period=period, status="PROCESSING"
    )
    db.add(task)
    db.commit()
    
    try:
        ticker_obj = yf.Ticker(ticker_clean)
        df = ticker_obj.history(period=period)
        
        if df.empty:
            task.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=422, detail="No historical records returned for criteria configurations.")
            
        # Clean records and scrub data arrays cleanly
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        
        formatted_history = []
        for index, row in df.iterrows():
            formatted_history.append({
                "date": index.strftime('%Y-%m-%d'),
                "open": round(float(row["Open"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })
            
        task.status = "COMPLETED"
        task.completed_at = datetime.datetime.utcnow()
        db.commit()
        
        return {
            "task_id": task.task_id,
            "ticker": ticker_clean,
            "company_name": ticker_obj.info.get("longName", ticker_clean),
            "historical_data": formatted_history[:50] # Returns active data points matrix
        }
    except Exception as e:
        task.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
