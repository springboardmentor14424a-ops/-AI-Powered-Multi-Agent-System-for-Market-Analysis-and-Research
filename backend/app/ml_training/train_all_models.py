"""
StockMind AI - Model Training Pipeline
Trains models for all analytical agents using the S&P 500 dataset:
1. Fundamental Analysis Agent Model:
   - Predicts company financial health & forward earnings performance (EPS growth / operating profitability)
   - Uses Random Forest Regressor & Gradient Boosting with sector embeddings
2. Technical Analysis Agent Model:
   - Trend & Direction Classifier (Up / Down next-day & 5-day horizon) based on multi-indicator features
   - Uses Random Forest / Gradient Boosting with RSI, MACD, Moving Averages, Volatility bands
3. Risk Analysis Agent Model:
   - Volatility & Max Drawdown Regressor / Risk Category Classifier
   - Estimates downside variance, Value-at-Risk (VaR), and Beta across market conditions
4. Sentiment & Market Intelligence Prioritizer:
   - Unsupervised & heuristic financial sentiment / anomaly detector on unusual volume & price dispersion
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score, classification_report
import joblib

DATA_DIR = Path("d:/infosys-project/data")
MODELS_DIR = Path("d:/infosys-project/backend/app/models_ml")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

metrics_report = {}

# ==============================================================================
# 1. Fundamental Analysis Agent Model Training
# ==============================================================================
print(">>> [1/3] Training Fundamental Analysis Agent Model...")

fund_path = DATA_DIR / "fundamentals.csv"
sec_path = DATA_DIR / "securities.csv"

fund_df = pd.read_csv(fund_path)
sec_df = pd.read_csv(sec_path)

# Merge GICS Sector
sec_subset = sec_df[['Ticker symbol', 'GICS Sector']].rename(columns={'Ticker symbol': 'Ticker Symbol'})
fund_df = fund_df.merge(sec_subset, on='Ticker Symbol', how='left')
fund_df['GICS Sector'] = fund_df['GICS Sector'].fillna('Unknown')

# Feature selection for fundamentals
fund_features = [
    'Gross Margin', 'Profit Margin', 'Pre-Tax Margin', 'Operating Margin',
    'Current Ratio', 'Quick Ratio', 'Cash Ratio', 'After Tax ROE', 'Pre-Tax ROE',
    'Total Assets', 'Total Liabilities', 'Total Revenue', 'Gross Profit',
    'Operating Income', 'Net Income', 'Cash and Cash Equivalents', 'Long-Term Debt'
]

# Clean and convert numeric
for col in fund_features + ['Earnings Per Share']:
    if col in fund_df.columns:
        fund_df[col] = pd.to_numeric(fund_df[col], errors='coerce')

# Target: Earnings Per Share (EPS) & Profitability Health
valid_fund = fund_df.dropna(subset=['Earnings Per Share', 'Total Revenue', 'Total Assets']).copy()

# Fill median for remaining feature nulls
for col in fund_features:
    valid_fund[col] = valid_fund[col].fillna(valid_fund[col].median())

# One-hot encode Sector
sector_dummies = pd.get_dummies(valid_fund['GICS Sector'], prefix='sector', drop_first=True)
X_fund = pd.concat([valid_fund[fund_features], sector_dummies], axis=1)
y_fund = valid_fund['Earnings Per Share']

# Also create a financial health rating target: 0 (Distressed), 1 (Stable), 2 (Strong)
# Based on Profit Margin, Current Ratio, and ROE
def classify_health(row):
    score = 0
    if row['Profit Margin'] > 10: score += 1
    if row['Current Ratio'] >= 1.5: score += 1
    if row['After Tax ROE'] > 12: score += 1
    if row['Net Income'] > 0: score += 1
    if score >= 3: return 2 # Strong
    elif score >= 1: return 1 # Stable
    return 0 # Distressed

y_fund_class = valid_fund.apply(classify_health, axis=1)

scaler_fund = StandardScaler()
X_fund_scaled = scaler_fund.fit_transform(X_fund)

# Train Regressor (EPS prediction)
X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X_fund_scaled, y_fund, test_size=0.2, random_state=42)
eps_model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
eps_model.fit(X_train_f, y_train_f)
y_pred_f = eps_model.predict(X_test_f)
r2_f = r2_score(y_test_f, y_pred_f)
rmse_f = np.sqrt(mean_squared_error(y_test_f, y_pred_f))

# Train Classifier (Health Rating)
X_train_fc, X_test_fc, y_train_fc, y_test_fc = train_test_split(X_fund_scaled, y_fund_class, test_size=0.2, random_state=42)
health_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
health_model.fit(X_train_fc, y_train_fc)
y_pred_fc = health_model.predict(X_test_fc)
acc_fc = accuracy_score(y_test_fc, y_pred_fc)

joblib.dump(eps_model, MODELS_DIR / "fundamental_eps_model.joblib")
joblib.dump(health_model, MODELS_DIR / "fundamental_health_model.joblib")
joblib.dump(scaler_fund, MODELS_DIR / "fundamental_scaler.joblib")
with open(MODELS_DIR / "fundamental_features.json", "w") as f:
    json.dump(list(X_fund.columns), f)

metrics_report["fundamental_analysis_agent"] = {
    "eps_regression": {"r2_score": round(float(r2_f), 4), "rmse": round(float(rmse_f), 4)},
    "health_classification": {"accuracy": round(float(acc_fc), 4), "classes": ["Distressed", "Stable", "Strong"]}
}
print(f"   Fundamental Models Trained -> EPS R2: {r2_f:.3f}, Health Acc: {acc_fc:.3f}")


# ==============================================================================
# 2. Technical Analysis Agent Model Training
# ==============================================================================
print(">>> [2/3] Training Technical Analysis Agent Model...")

prices_path = DATA_DIR / "prices-split-adjusted.csv"
prices_df = pd.read_csv(prices_path)
prices_df['date'] = pd.to_datetime(prices_df['date'])

# Sample top actively traded liquid stocks for technical pattern training across diverse sectors
top_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'JNJ', 'JPM', 'XOM', 'GE', 'WMT', 'BAC', 'PFE', 'INTC', 'CSCO', 'DIS']
sub_prices = prices_df[prices_df['symbol'].isin(top_tickers)].copy()
sub_prices = sub_prices.sort_values(by=['symbol', 'date'])

def calculate_technical_features(df):
    dfs = []
    for ticker, group in df.groupby('symbol'):
        g = group.copy()
        # Moving Averages
        g['sma_5'] = g['close'].rolling(window=5).mean()
        g['sma_10'] = g['close'].rolling(window=10).mean()
        g['sma_20'] = g['close'].rolling(window=20).mean()
        g['sma_50'] = g['close'].rolling(window=50).mean()

        # Ratios
        g['price_to_sma20'] = g['close'] / g['sma_20']
        g['sma5_to_sma20'] = g['sma_5'] / g['sma_20']

        # Volatility (Rolling standard deviation)
        g['volatility_20'] = g['close'].pct_change().rolling(window=20).std()

        # Momentum & Returns
        g['return_1d'] = g['close'].pct_change(1)
        g['return_5d'] = g['close'].pct_change(5)
        g['volume_ratio'] = g['volume'] / g['volume'].rolling(window=20).mean()

        # RSI (14 days)
        delta = g['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        g['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = g['close'].ewm(span=12, adjust=False).mean()
        ema26 = g['close'].ewm(span=26, adjust=False).mean()
        g['macd'] = ema12 - ema26
        g['macd_signal'] = g['macd'].ewm(span=9, adjust=False).mean()

        # Target: Forward 5-day direction (1 for UP >= +0.5%, 0 for Neutral/Down)
        g['forward_return_5d'] = g['close'].pct_change(5).shift(-5)
        g['target_direction'] = (g['forward_return_5d'] > 0.005).astype(int)

        dfs.append(g)
    return pd.concat(dfs, axis=0)

tech_data = calculate_technical_features(sub_prices)
tech_features = [
    'price_to_sma20', 'sma5_to_sma20', 'volatility_20', 'return_1d',
    'return_5d', 'volume_ratio', 'rsi_14', 'macd', 'macd_signal'
]

tech_clean = tech_data.dropna(subset=tech_features + ['target_direction', 'forward_return_5d']).copy()
X_tech = tech_clean[tech_features]
y_tech_class = tech_clean['target_direction']
y_tech_reg = tech_clean['forward_return_5d']

scaler_tech = StandardScaler()
X_tech_scaled = scaler_tech.fit_transform(X_tech)

# Train Technical Direction Classifier
X_train_t, X_test_t, y_train_t, y_test_t = train_test_split(X_tech_scaled, y_tech_class, test_size=0.2, random_state=42, shuffle=False)
tech_clf = RandomForestClassifier(n_estimators=120, max_depth=10, random_state=42, n_jobs=-1)
tech_clf.fit(X_train_t, y_train_t)
y_pred_t = tech_clf.predict(X_test_t)
acc_tech = accuracy_score(y_test_t, y_pred_t)
f1_tech = f1_score(y_test_t, y_pred_t, average='weighted')

# Train Technical Forward Return Regressor
tech_reg = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
tech_reg.fit(X_train_t, y_tech_reg.iloc[:len(X_train_t)])

joblib.dump(tech_clf, MODELS_DIR / "technical_direction_classifier.joblib")
joblib.dump(tech_reg, MODELS_DIR / "technical_return_regressor.joblib")
joblib.dump(scaler_tech, MODELS_DIR / "technical_scaler.joblib")
with open(MODELS_DIR / "technical_features.json", "w") as f:
    json.dump(tech_features, f)

metrics_report["technical_analysis_agent"] = {
    "direction_classification": {"accuracy": round(float(acc_tech), 4), "f1_score": round(float(f1_tech), 4)},
    "features_used": tech_features
}
print(f"   Technical Models Trained -> Acc: {acc_tech:.3f}, F1: {f1_tech:.3f}")


# ==============================================================================
# 3. Risk Analysis Agent Model Training
# ==============================================================================
print(">>> [3/3] Training Risk Analysis Agent Model...")

# Build risk profile metrics per stock across all 501 tickers:
# - Annualized Volatility
# - Max Drawdown
# - Value-at-Risk (95% Daily VaR)
# - Skewness & Kurtosis
risk_records = []
for ticker, grp in prices_df.groupby('symbol'):
    if len(grp) < 100:
        continue
    grp = grp.sort_values(by='date')
    daily_rets = grp['close'].pct_change().dropna()
    
    ann_vol = daily_rets.std() * np.sqrt(252)
    var_95 = np.percentile(daily_rets, 5) # 95% Daily VaR
    
    # Max Drawdown
    cum_rets = (1 + daily_rets).cumprod()
    peak = cum_rets.cummax()
    drawdown = (cum_rets - peak) / peak
    max_dd = drawdown.min()

    avg_volume = grp['volume'].mean()
    price_level = grp['close'].iloc[-1]
    
    risk_records.append({
        'symbol': ticker,
        'ann_volatility': ann_vol,
        'var_95': var_95,
        'max_drawdown': max_dd,
        'avg_volume': avg_volume,
        'price_level': price_level
    })

risk_df = pd.DataFrame(risk_records)
# Merge fundamental debt & sector features for risk modeling
fund_debt = fund_df.groupby('Ticker Symbol')[['Current Ratio', 'Long-Term Debt', 'Total Assets']].median().reset_index()
fund_debt = fund_debt.rename(columns={'Ticker Symbol': 'symbol'})
risk_combined = risk_df.merge(fund_debt, on='symbol', how='left')
risk_combined['debt_to_assets'] = (risk_combined['Long-Term Debt'] / (risk_combined['Total Assets'] + 1e-6)).fillna(0.3)
risk_combined['Current Ratio'] = risk_combined['Current Ratio'].fillna(1.5)

# Risk Category: 0: Low Risk, 1: Moderate Risk, 2: High Risk
def assign_risk_class(row):
    if row['ann_volatility'] > 0.35 or row['max_drawdown'] < -0.50:
        return 2 # High Risk
    elif row['ann_volatility'] < 0.22 and row['max_drawdown'] > -0.35:
        return 0 # Low Risk
    return 1 # Moderate Risk

risk_combined['risk_category'] = risk_combined.apply(assign_risk_class, axis=1)

risk_features = ['avg_volume', 'price_level', 'Current Ratio', 'debt_to_assets']
risk_clean = risk_combined.dropna(subset=risk_features + ['ann_volatility', 'risk_category']).copy()

X_risk = risk_clean[risk_features]
y_risk_vol = risk_clean['ann_volatility']
y_risk_class = risk_clean['risk_category']

scaler_risk = StandardScaler()
X_risk_scaled = scaler_risk.fit_transform(X_risk)

X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_risk_scaled, y_risk_class, test_size=0.2, random_state=42)
risk_clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
risk_clf.fit(X_train_r, y_train_r)
y_pred_r = risk_clf.predict(X_test_r)
acc_risk = accuracy_score(y_test_r, y_pred_r)

# Volatility Regressor
risk_reg = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
risk_reg.fit(X_risk_scaled, y_risk_vol)

joblib.dump(risk_clf, MODELS_DIR / "risk_category_classifier.joblib")
joblib.dump(risk_reg, MODELS_DIR / "risk_volatility_regressor.joblib")
joblib.dump(scaler_risk, MODELS_DIR / "risk_scaler.joblib")
with open(MODELS_DIR / "risk_features.json", "w") as f:
    json.dump(risk_features, f)

# Also save precomputed risk metrics per ticker for fast agent retrieval
risk_ticker_map = risk_combined.set_index('symbol')[['ann_volatility', 'var_95', 'max_drawdown', 'risk_category']].to_dict(orient='index')
with open(MODELS_DIR / "risk_ticker_profiles.json", "w") as f:
    json.dump(risk_ticker_map, f)

metrics_report["risk_analysis_agent"] = {
    "risk_classification": {"accuracy": round(float(acc_risk), 4), "risk_levels": ["Low Risk", "Moderate Risk", "High Risk"]},
    "volatility_regressor": "Trained",
    "tickers_profiled": len(risk_ticker_map)
}
print(f"   Risk Models Trained -> Acc: {acc_risk:.3f}, Profiled Tickers: {len(risk_ticker_map)}")

# Save final metrics report
with open(MODELS_DIR / "training_metrics.json", "w") as f:
    json.dump(metrics_report, f, indent=2)

print("\n>>> ALL MODELS SUCCESSFULLY TRAINED AND SAVED TO:", str(MODELS_DIR))
