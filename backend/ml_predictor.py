import os
import json
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import HTTPException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, "ml_model")

MODEL_PATH = os.path.join(ML_DIR, "best_stock_model.pkl")
SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
META_PATH = os.path.join(ML_DIR, "model_metadata.json")

_model = None
_scaler = None
_meta = None


def _load_artifacts():
    global _model, _scaler, _meta
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(status_code=500, detail="ML model file not found. Run the notebook first.")
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        with open(META_PATH, "r") as f:
            _meta = json.load(f)


def resolve_ticker(symbol: str, market: str) -> str:
    sym = symbol.strip().upper()
    if "." in sym:
        return sym
    if market.upper() == "NSE":
        return f"{sym}.NS"
    if market.upper() == "BSE":
        return f"{sym}.BO"
    return sym


def predict_stock_trend(symbol: str, market: str = "NSE") -> dict:
    _load_artifacts()
    resolved = resolve_ticker(symbol, market)

    hist = yf.Ticker(resolved).history(period="3mo")
    if hist.empty or len(hist) < 25:
        raise HTTPException(status_code=404, detail=f"Not enough historical data for {resolved}")

    df = hist.copy().reset_index()
    df["Prev Close"] = df["Close"].shift(1)
    df["VWAP"] = (df["High"] + df["Low"] + df["Close"]) / 3.0

    # Exact 15 features from your training notebook
    df["daily_return"] = (df["Close"] - df["Open"]) / df["Open"]
    df["high_low_pct"] = (df["High"] - df["Low"]) / df["Low"]
    df["open_prev_gap"] = (df["Open"] - df["Prev Close"]) / df["Prev Close"]
    df["close_to_vwap"] = df["Close"] / df["VWAP"]

    df["ma_5"] = df["Close"].rolling(5).mean()
    df["ma_20"] = df["Close"].rolling(20).mean()
    df["volatility_5"] = df["daily_return"].rolling(5).std()

    df["price_to_ma5"] = df["Close"] / df["ma_5"]
    df["ma5_to_ma20"] = df["ma_5"] / df["ma_20"]

    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    if df.empty:
        raise HTTPException(status_code=400, detail="Could not compute features for this symbol.")

    latest = df.iloc[[-1]][_meta["features"]]
    X_input = _scaler.transform(latest) if _meta.get("uses_scaled") else latest

    pred = int(_model.predict(X_input)[0])
    proba = _model.predict_proba(X_input)[0] if hasattr(_model, "predict_proba") else [0.5, 0.5]
    confidence = round(float(max(proba)) * 100, 2)

    return {
        "symbol": resolved,
        "prediction": "Bullish" if pred == 1 else "Bearish",
        "confidence_pct": confidence,
        "latest_close": round(float(df.iloc[-1]["Close"]), 2),
        "model_name": _meta["model_name"],
        "model_accuracy_pct": _meta["accuracy_pct"],
    }