from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from database import engine, get_db
import models
import schemas
import pandas as pd
import yfinance as yf
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from fastapi.responses import RedirectResponse
import os
import secrets
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from pathlib import Path
import joblib
from pydantic import BaseModel

# Automatically create tables if non-existent
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "notebooks"/ "artifacts"

rf_model = joblib.load(ARTIFACT_DIR / "nse_rf_model.joblib")
rf_scaler = joblib.load(ARTIFACT_DIR / "nse_scaler.joblib")
rf_features = joblib.load(ARTIFACT_DIR / "nse_feature_cols.joblib")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your_super_secret_key"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OAuth
config = Config(environ=os.environ)
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

# Secret key to sign JWT (keep this secret in production!)
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode and verify token signature and expiry
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Protected endpoint that requires a valid JWT token
@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active
    }

@app.get("/")
def read_root():
    return {"message": "FastAPI is successfully connected to PostgreSQL!"}


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # 1. Hash the password
        hashed_pwd = hash_password(user.password)

        # 2. Creating new user database model instance
        new_user = models.User(
            email=user.email,
            hashed_password=hashed_pwd
        )

        # 3. Saving to PostgreSQL
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form_data.username holds the email input from Swagger/frontend
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect email or password"
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = "http://localhost:8001/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    
    # Fetching user info directly from Google's userinfo endpoint
    resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
    user_info = resp.json()
    
    if not user_info or 'email' not in user_info:
        raise HTTPException(status_code=400, detail="Google authentication failed")

    email = user_info['email']
    full_name = user_info.get('name', 'Google User')
    
    # Checking if user already exists in DB
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        hashed_password = pwd_context.hash(secrets.token_hex(16))
        user = models.User(email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(data={"sub": email})
    return RedirectResponse(url=f"http://localhost:5173/research?token={access_token}")

def process_research_task(task_id: int, db: Session):
    task = db.query(models.ResearchTask).filter(models.ResearchTask.id == task_id).first()
    if not task:
        return

    try:
        ticker_symbol = task.ticker
        period = task.requested_period or "1y"
        
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period)

        if hist.empty:
            task.status = "Failed"
            db.commit()
            return

        latest_close = float(hist['Close'].iloc[-1])
        task.status = "Completed"
        db.commit()
    except Exception as e:
        task.status = "Failed"
        db.commit()
        print(f"Error processing task {task_id}: {e}")

def format_ticker_for_market(raw_ticker: str, market: str | None) -> str:
    symbol = raw_ticker.strip().upper()
    mkt = (market or "").strip().upper()

    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol

    if "NSE" in mkt:
        return f"{symbol}.NS"
    if "BSE" in mkt:
        return f"{symbol}.BO"
    return symbol

@app.post("/research")
def create_research_task(task: schemas.ResearchTaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # Fetching live ticker data via yfinance using the requested period from frontend
        formatted_ticker = format_ticker_for_market(task.ticker, task.market)
        print("DEBUG -> ticker:", task.ticker, "| market:", task.market, "| formatted:", formatted_ticker)
        stock = yf.Ticker(formatted_ticker)
        hist = stock.history(period=task.requested_period)
        
        if hist.empty:
            raise HTTPException(status_code=400, detail="Invalid ticker symbol or no data available.")

        info = stock.info or {}
        company_profile = {
            "company_name": info.get("longName") or info.get("shortName") or task.ticker.upper(),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "summary": info.get("longBusinessSummary", "No business summary available."),
            "market_cap": info.get("marketCap"),
            "website": info.get("website", "N/A")
        }

        # 2. Financial Statements (Income Statement / Financials)
        financials_list = []
        try:
            fin_df = stock.income_stmt
            if fin_df is None or fin_df.empty:
                fin_df = stock.financials
            if fin_df is not None and not fin_df.empty:
                # Grab top key metrics (Revenue, Net Income, Gross Profit) across available years
                target_metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"]
                available_metrics = [m for m in target_metrics if m in fin_df.index]

                if not available_metrics:
                    available_metrics = list(fin_df.index[:4])
        
                for metric in available_metrics:
                    row_data = {"metric": metric}
                    for col_date in fin_df.columns[:3]:  # Last 3 fiscal years
                        val = fin_df.loc[metric, col_date]
                        date_str = col_date.strftime("%Y-%m-%d") if hasattr(col_date, "strftime") else str(col_date)
                        row_data[date_str] = None if pd.isna(val) else float(val)
                    financials_list.append(row_data)
        except Exception as e:
            print(f"Financials fetch warning for {task.ticker}: {e}")

        # 3. Data Source & Retrieval Timestamp
        metadata = {
        "source": "Yahoo Finance (yfinance)",
        "retrieved_at": datetime.now(timezone.utc).isoformat()
        }

        # Getting latest close price and company name
        latest_close = float(hist['Close'].iloc[-1])
        company_name = stock.info.get('shortName', task.ticker.upper())

        # Formatting OHLCV rows for your new frontend table
        hist_reset = hist.reset_index()
        ohlcv_list = []
        for _, row in hist_reset.iterrows():
            ohlcv_list.append({
                "Date": row['Date'].strftime('%Y-%m-%d'),
                "Open": float(row['Open']),
                "High": float(row['High']),
                "Low": float(row['Low']),
                "Close": float(row['Close']),
                "Volume": int(row['Volume'])
            })

        # Saving the research task to the database as Completed
        new_task = models.ResearchTask(
            ticker=task.ticker.strip().upper(),
            market=task.market,
            requested_period=task.requested_period,
            status="Completed",
            user_id=current_user.id
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        # Return the complete payload your frontend UI table is waiting for
        return {
            "id": new_task.id,
            "ticker": new_task.ticker.strip().upper(),
            "market": new_task.market,
            "requested_period": new_task.requested_period,
            "company_name": company_name,
            "result_price": latest_close,
            "status": "Completed",
            "ohlcv": ohlcv_list,
            "profile": company_profile,
            "financials": financials_list,
            "source": metadata["source"],
            "retrieved_at": metadata["retrieved_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch market data: {str(e)}")
        
@app.get("/research/history")
def get_research_history(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Returning only the logged-in user's research tasks
    tasks = db.query(models.ResearchTask).filter(models.ResearchTask.user_id == current_user.id).all()
    return tasks

def validate_and_format_ticker(ticker: str, market: str):
    ticker = ticker.upper().strip()
    
    if market == "NSE":
        query_ticker = f"{ticker}.NS" if not ticker.endswith(".NS") else ticker
    elif market == "BSE":
        query_ticker = f"{ticker}.BO" if not ticker.endswith(".BO") else ticker
    else:
        query_ticker = ticker

    try:
        stock = yf.Ticker(query_ticker)
        hist = stock.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=400, detail=f"Invalid ticker symbol '{ticker}' for market {market}.")
        return query_ticker
    except HTTPException as he:
        raise he
    except Exception:
        raise HTTPException(status_code=400, detail=f"Could not validate ticker '{ticker}' with Yahoo Finance for {market}.")

@app.get("/watchlist", response_model=list[schemas.WatchlistResponse])
def get_watchlist(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user.id).all()

@app.post("/watchlist", response_model=schemas.WatchlistResponse)
def add_to_watchlist(item: schemas.WatchlistCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    validated_ticker = validate_and_format_ticker(item.ticker, item.market)

    existing = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.ticker == validated_ticker,
        models.Watchlist.market == item.market
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ticker already in watchlist for this market")

    new_item = models.Watchlist(
        user_id=current_user.id,
        ticker=validated_ticker,
        market=item.market
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.delete("/watchlist/{item_id}")
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Watchlist).filter(
        models.Watchlist.id == item_id,
        models.Watchlist.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}

@app.get("/preferences", response_model=schemas.UserPreferencesResponse)
def get_user_preferences(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == current_user.id).first()
    if not prefs:
        # Creating default preferences if none exist yet
        prefs = models.UserPreferences(user_id=current_user.id, default_market="NASDAQ", default_period="1y")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@app.put("/preferences", response_model=schemas.UserPreferencesResponse)
def update_user_preferences(prefs_update: schemas.UserPreferencesUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = models.UserPreferences(user_id=current_user.id)
        db.add(prefs)
    
    prefs.default_market = prefs_update.default_market
    prefs.default_period = prefs_update.default_period
    db.commit()
    db.refresh(prefs)
    return prefs

@app.get("/api/search/{ticker}")
def search_company(ticker: str):
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        # Checking if the ticker actually exists by looking for a valid field
        if not info or "regularMarketPrice" in info and info["regularMarketPrice"] is None and "longBusinessSummary" not in info:
            raise HTTPException(status_code=404, detail="Company or ticker not found.")
            
        return {
            "symbol": ticker.upper(),
            "shortName": info.get("shortName", info.get("longName", "N/A")),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error fetching data: {str(e)}")

class StockPredictionInput(BaseModel):
  features: dict[str, float]

@app.post("/predict")
def predict_from_model(payload: StockPredictionInput):
  row = {col: float(payload.features.get(col, 0.0)) for col in rf_features}
  X_input = pd.DataFrame([row])[rf_features]
  X_scaled = rf_scaler.transform(X_input)
  prediction = float(rf_model.predict(X_scaled)[0])
  return {
      "predicted_close": prediction,
      "features_used": rf_features,
  }