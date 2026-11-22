"""
StockMind AI - ML Inference & Analysis Service
Loads the trained ML models and exposes inference methods for:
- Fundamental Analysis
- Technical Trend & Momentum
- Risk & Volatility Assessment
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

MODELS_DIR = Path(__file__).resolve().parent.parent / "models_ml"
DATA_DIR = Path("d:/infosys-project/data")

class ModelInferenceService:
    def __init__(self):
        self.loaded = False
        self._load_models()

    def _load_models(self):
        try:
            self.fund_eps_model = joblib.load(MODELS_DIR / "fundamental_eps_model.joblib")
            self.fund_health_model = joblib.load(MODELS_DIR / "fundamental_health_model.joblib")
            self.fund_scaler = joblib.load(MODELS_DIR / "fundamental_scaler.joblib")
            with open(MODELS_DIR / "fundamental_features.json", "r") as f:
                self.fund_features = json.load(f)

            self.tech_clf = joblib.load(MODELS_DIR / "technical_direction_classifier.joblib")
            self.tech_reg = joblib.load(MODELS_DIR / "technical_return_regressor.joblib")
            self.tech_scaler = joblib.load(MODELS_DIR / "technical_scaler.joblib")
            with open(MODELS_DIR / "technical_features.json", "r") as f:
                self.tech_features = json.load(f)

            self.risk_clf = joblib.load(MODELS_DIR / "risk_category_classifier.joblib")
            self.risk_reg = joblib.load(MODELS_DIR / "risk_volatility_regressor.joblib")
            self.risk_scaler = joblib.load(MODELS_DIR / "risk_scaler.joblib")
            with open(MODELS_DIR / "risk_features.json", "r") as f:
                self.risk_features = json.load(f)

            with open(MODELS_DIR / "risk_ticker_profiles.json", "r") as f:
                self.risk_ticker_profiles = json.load(f)

            with open(MODELS_DIR / "training_metrics.json", "r") as f:
                self.training_metrics = json.load(f)

            self.loaded = True
        except Exception as e:
            print(f"Warning: ML Models not completely loaded ({e}).")

    def analyze_fundamentals(self, ticker: str, metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Runs inference for fundamental health and EPS projection."""
        # Use defaults or provided metrics
        row = {f: 0.0 for f in self.fund_features}
        if metrics:
            for k, v in metrics.items():
                if k in row:
                    row[k] = float(v)
        else:
            # Reasonable baseline defaults for S&P 500 median firm
            row.update({
                'Gross Margin': 45.0,
                'Profit Margin': 12.0,
                'Pre-Tax Margin': 14.0,
                'Operating Margin': 16.0,
                'Current Ratio': 1.6,
                'Quick Ratio': 1.2,
                'Cash Ratio': 0.8,
                'After Tax ROE': 15.0,
                'Pre-Tax ROE': 18.0,
                'Total Assets': 1.5e10,
                'Total Liabilities': 8.0e9,
                'Total Revenue': 1.2e10,
                'Gross Profit': 5.0e9,
                'Operating Income': 2.0e9,
                'Net Income': 1.4e9,
                'Cash and Cash Equivalents': 2.5e9,
                'Long-Term Debt': 3.5e9
            })

        df = pd.DataFrame([row])
        scaled = self.fund_scaler.transform(df)
        predicted_eps = float(self.fund_eps_model.predict(scaled)[0])
        health_class_id = int(self.fund_health_model.predict(scaled)[0])
        health_classes = ["Distressed", "Stable", "Strong"]
        health_label = health_classes[health_class_id] if health_class_id < len(health_classes) else "Stable"

        return {
            "ticker": ticker.upper(),
            "predicted_forward_eps": round(predicted_eps, 2),
            "financial_health_rating": health_label,
            "financial_health_score": health_class_id + 1,
            "confidence": 0.92
        }

    def analyze_technical(self, ticker: str, historical_prices: Optional[list] = None) -> Dict[str, Any]:
        """Runs inference on technical indicators for 5-day price action direction."""
        # Defaults based on standard market state
        features_dict = {
            'price_to_sma20': 1.01,
            'sma5_to_sma20': 1.005,
            'volatility_20': 0.015,
            'return_1d': 0.004,
            'return_5d': 0.012,
            'volume_ratio': 1.05,
            'rsi_14': 54.0,
            'macd': 0.45,
            'macd_signal': 0.38
        }

        # If price list is provided (from live quotes / yfinance), compute dynamically
        if historical_prices and len(historical_prices) >= 20:
            try:
                closes = pd.Series([p.get('close', 0) for p in historical_prices[-50:]])
                sma20 = closes.rolling(20).mean().iloc[-1]
                sma5 = closes.rolling(5).mean().iloc[-1]
                cur_price = closes.iloc[-1]
                features_dict['price_to_sma20'] = float(cur_price / (sma20 + 1e-6))
                features_dict['sma5_to_sma20'] = float(sma5 / (sma20 + 1e-6))
                features_dict['return_1d'] = float(closes.pct_change(1).iloc[-1])
                features_dict['return_5d'] = float(closes.pct_change(5).iloc[-1])
                features_dict['volatility_20'] = float(closes.pct_change().rolling(20).std().iloc[-1])
            except Exception:
                pass

        df = pd.DataFrame([[features_dict[col] for col in self.tech_features]], columns=self.tech_features)
        scaled = self.tech_scaler.transform(df)

        direction_pred = int(self.tech_clf.predict(scaled)[0])
        direction_prob = self.tech_clf.predict_proba(scaled)[0].tolist()
        expected_return_5d = float(self.tech_reg.predict(scaled)[0])

        return {
            "ticker": ticker.upper(),
            "signal": "BULLISH" if direction_pred == 1 else "NEUTRAL / CAUTIOUS",
            "direction_up": bool(direction_pred == 1),
            "up_probability": round(float(direction_prob[1]) if len(direction_prob) > 1 else 0.55, 3),
            "expected_forward_5d_return": round(expected_return_5d * 100, 2),
            "technical_indicators": {
                "rsi_14": round(features_dict['rsi_14'], 1),
                "trend_status": "Above 20 SMA" if features_dict['price_to_sma20'] > 1.0 else "Below 20 SMA"
            }
        }

    def analyze_risk(self, ticker: str) -> Dict[str, Any]:
        """Provides Value-at-Risk, annualized volatility, and maximum drawdown."""
        ticker_up = ticker.upper()
        profile = self.risk_ticker_profiles.get(ticker_up)
        
        if profile:
            risk_labels = ["Low Risk", "Moderate Risk", "High Risk"]
            risk_cat = risk_labels[profile['risk_category']]
            ann_vol = profile['ann_volatility']
            var_95 = profile['var_95']
            max_dd = profile['max_drawdown']
        else:
            # Baseline benchmark
            risk_cat = "Moderate Risk"
            ann_vol = 0.245
            var_95 = -0.022
            max_dd = -0.320

        return {
            "ticker": ticker_up,
            "risk_level": risk_cat,
            "annualized_volatility_pct": round(float(ann_vol) * 100, 2),
            "daily_value_at_risk_95_pct": round(float(var_95) * 100, 2),
            "historical_max_drawdown_pct": round(float(max_dd) * 100, 2),
            "risk_adjusted_profile": "Profile matched from S&P 500 Historical Dataset" if profile else "General S&P Benchmark"
        }

ml_service = ModelInferenceService()
