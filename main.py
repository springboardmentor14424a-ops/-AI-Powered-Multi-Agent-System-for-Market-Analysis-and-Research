from datetime import datetime, timedelta, timezone
import math
import os
from pathlib import Path
import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import joblib
from jose import JWTError, jwt
import numpy as np
import pandas as pd
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import yfinance as yf

from agents import FundamentalAnalysisAgent
from database import engine, get_db
import models
import schemas

# Automatically create tables if non-existent
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "notebooks" / "artifacts"
CLF_ARTIFACT_DIR = BASE_DIR / "notebooks" / "artifacts"


def _safe_joblib_load(path: Path, default=None):
    try:
        if path.exists():
            return joblib.load(path)
    except Exception as exc:
        print(f"Artifact load warning for {path}: {exc}")
    return default


rf_model = _safe_joblib_load(ARTIFACT_DIR / "nse_rf_model.joblib")
rf_scaler = _safe_joblib_load(ARTIFACT_DIR / "nse_scaler.joblib")
rf_features = _safe_joblib_load(ARTIFACT_DIR / "nse_feature_cols.joblib", [])

gb_clf_model = _safe_joblib_load(CLF_ARTIFACT_DIR / "nse_gb_clf_model.joblib")
clf_scaler = _safe_joblib_load(CLF_ARTIFACT_DIR / "nse_clf_scaler.joblib")
clf_features = _safe_joblib_load(CLF_ARTIFACT_DIR / "nse_clf_features.joblib", [])

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
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


# Secret key to sign JWT (keep this secret in production!)
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_dev_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
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


@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
    }


@app.get("/")
def read_root():
    return {"message": "FastAPI is successfully connected to PostgreSQL!"}


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        hashed_pwd = hash_password(user.password)
        new_user = models.User(
            email=user.email,
            hashed_password=hashed_pwd,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect email or password",
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
    resp = await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)
    user_info = resp.json()

    if not user_info or "email" not in user_info:
        raise HTTPException(status_code=400, detail="Google authentication failed")

    email = user_info["email"]

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


def _clean_float(val):
    if val is None or pd.isna(val):
        return None
    f = float(val)
    return None if (math.isnan(f) or math.isinf(f)) else f


def _clean_int(val):
    if val is None or pd.isna(val):
        return None
    f = float(val)
    if math.isnan(f) or math.isinf(f):
        return None
    return int(f)


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if obj is not None and not isinstance(obj, (str, bool, int)):
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass
    return obj


@app.post("/research")
def create_research_task(
    task: schemas.ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        formatted_ticker = format_ticker_for_market(task.ticker, task.market)
        print("DEBUG -> ticker:", task.ticker, "| market:", task.market, "| formatted:", formatted_ticker)
        stock = yf.Ticker(formatted_ticker)
        hist = stock.history(period=task.requested_period)

        if hist is None or hist.empty:
            raise HTTPException(status_code=400, detail="Invalid ticker symbol or no data available.")

        valid_close = hist["Close"].dropna() if "Close" in hist.columns else pd.Series(dtype=float)
        latest_close = _clean_float(valid_close.iloc[-1]) if not valid_close.empty else None

        try:
            info = stock.info or {}
        except Exception as e:
            print(f"stock.info warning for {formatted_ticker}: {e}")
            info = {}

        company_profile = {
            "company_name": info.get("longName") or info.get("shortName") or task.ticker.strip().upper(),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "summary": info.get("longBusinessSummary", "No business summary available."),
            "market_cap": _clean_float(info.get("marketCap")),
            "website": info.get("website", "N/A"),
        }

        financials_list = []
        try:
            fin_df = stock.income_stmt
            if fin_df is None or fin_df.empty:
                fin_df = stock.financials
            if fin_df is not None and not fin_df.empty:
                target_metrics = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"]
                available_metrics = [m for m in target_metrics if m in fin_df.index]

                if not available_metrics:
                    available_metrics = list(fin_df.index[:4])

                for metric in available_metrics:
                    row_data = {"metric": metric}
                    for col_date in fin_df.columns[:3]:
                        val = fin_df.loc[metric, col_date]
                        date_str = col_date.strftime("%Y-%m-%d") if hasattr(col_date, "strftime") else str(col_date)
                        row_data[date_str] = _clean_float(val)
                    financials_list.append(row_data)
        except Exception as e:
            print(f"Financials fetch warning for {task.ticker}: {e}")

        metadata = {
            "source": "Yahoo Finance (yfinance)",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

        company_name = info.get("shortName") or info.get("longName") or task.ticker.strip().upper()

        hist_reset = hist.reset_index()
        ohlcv_list = []
        date_col = "Date" if "Date" in hist_reset.columns else hist_reset.columns[0]
        for _, row in hist_reset.iterrows():
            dt_val = row[date_col]
            date_str = dt_val.strftime("%Y-%m-%d") if hasattr(dt_val, "strftime") else str(dt_val)
            ohlcv_list.append({
                "Date": date_str,
                "Open": _clean_float(row.get("Open")),
                "High": _clean_float(row.get("High")),
                "Low": _clean_float(row.get("Low")),
                "Close": _clean_float(row.get("Close")),
                "Volume": _clean_int(row.get("Volume")),
            })

        new_task = models.ResearchTask(
            ticker=task.ticker.strip().upper(),
            market=task.market,
            requested_period=task.requested_period,
            status="Completed",
            user_id=current_user.id,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        payload = {
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
        return sanitize_for_json(payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch market data: {str(e)}")


@app.get("/research/history")
def get_research_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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
def add_to_watchlist(
    item: schemas.WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    validated_ticker = validate_and_format_ticker(item.ticker, item.market)

    existing = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.ticker == validated_ticker,
        models.Watchlist.market == item.market,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Ticker already in watchlist for this market")

    new_item = models.Watchlist(
        user_id=current_user.id,
        ticker=validated_ticker,
        market=item.market,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@app.delete("/watchlist/{item_id}")
def remove_from_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = db.query(models.Watchlist).filter(
        models.Watchlist.id == item_id,
        models.Watchlist.user_id == current_user.id,
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
        prefs = models.UserPreferences(user_id=current_user.id, default_market="NASDAQ", default_period="1y")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@app.put("/preferences", response_model=schemas.UserPreferencesResponse)
def update_user_preferences(
    prefs_update: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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

        if not info or ("regularMarketPrice" in info and info["regularMarketPrice"] is None and "longBusinessSummary" not in info):
            raise HTTPException(status_code=404, detail="Company or ticker not found.")

        return {
            "symbol": ticker.upper(),
            "shortName": info.get("shortName", info.get("longName", "N/A")),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A"),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error fetching data: {str(e)}")


class StockPredictionInput(BaseModel):
    features: dict[str, float]


@app.post("/predict")
def predict_from_model(payload: StockPredictionInput):
    if rf_model is None or rf_scaler is None:
        raise HTTPException(status_code=500, detail="Random forest model artifacts not loaded.")
    row = {col: float(payload.features.get(col, 0.0)) for col in rf_features}
    X_input = pd.DataFrame([row])[rf_features]
    X_scaled = rf_scaler.transform(X_input)
    prediction = float(rf_model.predict(X_scaled)[0])
    return {
        "predicted_close": prediction,
        "features_used": rf_features,
    }


class DirectionRequest(BaseModel):
    features: dict[str, float]


@app.post("/predict-direction")
def predict_direction(payload: DirectionRequest):
    if gb_clf_model is None or clf_scaler is None:
        raise HTTPException(status_code=500, detail="Gradient boosting classifier artifacts not loaded.")
    row = [[float(payload.features.get(col, 0.0)) for col in clf_features]]
    scaled_row = clf_scaler.transform(row)

    pred_up = int(gb_clf_model.predict(scaled_row)[0])
    prob_up = (
        float(gb_clf_model.predict_proba(scaled_row)[0][1])
        if hasattr(gb_clf_model, "predict_proba")
        else None
    )

    return {
        "model": "GradientBoostingClassifier",
        "target_up": pred_up,
        "direction": "UP (Close > Open)" if pred_up == 1 else "NOT UP (Close <= Open)",
        "confidence_up": round(prob_up, 4) if prob_up is not None else None,
    }


class TrendPredictRequest(BaseModel):
    ticker: str
    market: str | None = "NSE"


@app.post("/predict/trend")
def predict_trend_from_ticker(payload: TrendPredictRequest):
    if gb_clf_model is None or clf_scaler is None or not clf_features:
        raise HTTPException(status_code=500, detail="Gradient boosting classifier artifacts not loaded.")

    formatted_ticker = format_ticker_for_market(payload.ticker, payload.market)
    hist = yf.Ticker(formatted_ticker).history(period="3mo", interval="1d")
    if hist is None or hist.empty:
        raise HTTPException(status_code=400, detail=f"No historical market data found for {formatted_ticker}.")

    df_feat = hist.copy().reset_index()
    df_feat.columns = [str(c).strip() for c in df_feat.columns]

    open_s = pd.to_numeric(df_feat.get("Open"), errors="coerce")
    high_s = pd.to_numeric(df_feat.get("High"), errors="coerce")
    low_s = pd.to_numeric(df_feat.get("Low"), errors="coerce")
    close_s = pd.to_numeric(df_feat.get("Close"), errors="coerce")
    vol_s = pd.to_numeric(df_feat.get("Volume"), errors="coerce")

    alias_map = {
        "Open": open_s,
        "High": high_s,
        "Low": low_s,
        "Close": close_s,
        "Volume": vol_s,
        "Total Traded Quantity": vol_s,
        "TotTrdQty": vol_s,
        "intraday_range": high_s - low_s,
    }

    row_dict = {}
    for col in clf_features:
        if col in df_feat.columns:
            s = pd.to_numeric(df_feat[col], errors="coerce").ffill().bfill().fillna(0.0)
            row_dict[col] = float(s.iloc[-1])
        elif col in alias_map:
            s = pd.to_numeric(alias_map[col], errors="coerce").ffill().bfill().fillna(0.0)
            row_dict[col] = float(s.iloc[-1])
        else:
            row_dict[col] = 0.0

    X_df = pd.DataFrame([row_dict], columns=clf_features).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    scaled_row = clf_scaler.transform(X_df)

    pred_up = int(gb_clf_model.predict(scaled_row)[0])
    prob_up = (
        float(gb_clf_model.predict_proba(scaled_row)[0][1])
        if hasattr(gb_clf_model, "predict_proba")
        else None
    )

    latest_close = _clean_float(close_s.dropna().iloc[-1]) if not close_s.dropna().empty else None
    confidence_pct = round(prob_up * 100.0, 2) if prob_up is not None else None

    return sanitize_for_json({
        "ticker": payload.ticker.strip().upper(),
        "market": (payload.market or "NSE").strip().upper(),
        "model": "GradientBoostingClassifier (nse_gb_clf_model)",
        "target_up": pred_up,
        "prediction": "Bullish (UP)" if pred_up == 1 else "Bearish (NOT UP)",
        "direction": "UP (Close > Open)" if pred_up == 1 else "NOT UP (Close <= Open)",
        "confidence": confidence_pct,
        "confidence_up": round(prob_up, 4) if prob_up is not None else None,
        "latest_close": latest_close,
    })


fundamental_agent = FundamentalAnalysisAgent()


class FundamentalAnalysisRequest(BaseModel):
    ticker: str
    market: str | None = None


@app.post("/analyze/fundamentals")
def analyze_fundamentals(payload: FundamentalAnalysisRequest):
    try:
        return fundamental_agent.run(payload.ticker, payload.market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed fundamental analysis: {str(e)}")