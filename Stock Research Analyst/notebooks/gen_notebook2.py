"""
Generate notebooks/02_features_analysis.ipynb
Each feature = its own cell, plus live Yahoo Finance API integration cell.
"""
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
import os

nb = new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3 (venv)",
        "language": "python",
        "name": "python3"
    },
    "language_info": {"name": "python", "version": "3.11.0"}
}

cells = []

# ── Cell 1: Imports & Load Data ────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 1 — Imports & Load Dataset"))
cells.append(new_code_cell("""
import os, glob, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings('ignore')
sns.set_theme(style='darkgrid', palette='muted')
pd.set_option('display.float_format', '{:.2f}'.format)

# ── Load all Stock files ──────────────────────────────────────────────────
DATA_DIR = os.path.join('..', 'archive_data')
stock_files = glob.glob(os.path.join(DATA_DIR, 'Stock_*.xlsx'))
print(f"Loading {len(stock_files)} stock files...")

dfs = []
for f in stock_files:
    ticker = os.path.basename(f).replace('Stock_', '').replace('.xlsx', '')
    df_tmp = pd.read_excel(f)
    df_tmp['Ticker'] = ticker
    dfs.append(df_tmp)

raw = pd.concat(dfs, ignore_index=True)
raw.columns = [c.strip().title() for c in raw.columns]

# Map to standard names
col_map = {}
for c in raw.columns:
    cl = c.lower()
    if 'date' in cl: col_map[c] = 'Date'
    elif 'open' in cl: col_map[c] = 'Open'
    elif 'high' in cl: col_map[c] = 'High'
    elif 'low' in cl: col_map[c] = 'Low'
    elif 'close' in cl and 'prev' not in cl: col_map[c] = 'Close'
    elif 'volume' in cl or cl == 'vol': col_map[c] = 'Volume'
    elif c == 'Ticker': col_map[c] = 'Ticker'
raw = raw.rename(columns=col_map)

if 'Date' in raw.columns:
    raw['Date'] = pd.to_datetime(raw['Date'], errors='coerce')
    raw = raw.sort_values(['Ticker', 'Date']).reset_index(drop=True)

print(f"Dataset: {len(raw):,} rows, columns: {list(raw.columns)}")
raw.head()
"""))

# ── Cell 2: Revenue & Earnings Analysis ───────────────────────────────────
cells.append(new_markdown_cell("""---
## Cell 2 — Feature 1: Revenue & Earnings Analysis

This cell analyses revenue-proxy metrics (annual Close-price as revenue proxy from OHLCV)
and calculates earnings-related indicators from OHLCV data.
"""))
cells.append(new_code_cell("""
# ── Revenue & Earnings Analysis ───────────────────────────────────────────
# Since the archive is OHLCV data (not P&L), we derive revenue-proxy signals:
#   • Annual median closing price  → proxy for market-valued "revenue" per share
#   • Year-over-Year price growth  → earnings / revenue growth signal
#   • Turnover (Close × Volume)    → revenue throughput proxy

df = raw.copy().dropna(subset=['Date', 'Close'])
df['Year'] = df['Date'].dt.year

# Compute annual stats per ticker
annual = df.groupby(['Ticker', 'Year']).agg(
    Avg_Close=('Close', 'mean'),
    Total_Volume=('Volume', 'sum') if 'Volume' in df.columns else ('Close', 'count'),
).reset_index()

if 'Volume' in df.columns:
    annual_turn = df.groupby(['Ticker', 'Year']).apply(
        lambda g: (g['Close'] * g['Volume']).sum()
    ).reset_index(name='Turnover')
    annual = annual.merge(annual_turn, on=['Ticker', 'Year'])
    annual['Turnover_Cr'] = annual['Turnover'] / 1e7   # in Crores

# YoY Growth (revenue-proxy)
annual = annual.sort_values(['Ticker', 'Year'])
annual['YoY_Growth_Pct'] = annual.groupby('Ticker')['Avg_Close'].pct_change() * 100

# ── Plots ─────────────────────────────────────────────────────────────────
top_tickers = annual.groupby('Ticker')['Avg_Close'].max().nlargest(6).index.tolist()

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('Revenue & Earnings Analysis (OHLCV-based Proxies)', fontsize=15, fontweight='bold')

# 1. Annual avg close for top tickers
ax = axes[0, 0]
for t in top_tickers:
    sub = annual[annual['Ticker'] == t]
    ax.plot(sub['Year'], sub['Avg_Close'], marker='o', label=t)
ax.set_title('Annual Avg Close Price — Top 6 Tickers')
ax.set_xlabel('Year'); ax.set_ylabel('Avg Close (₹)')
ax.legend(fontsize=8); ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'₹{x:,.0f}'))

# 2. YoY Growth distribution
ax = axes[0, 1]
yoy_clean = annual['YoY_Growth_Pct'].dropna().clip(-80, 150)
ax.hist(yoy_clean, bins=50, color='steelblue', edgecolor='white', alpha=0.8)
ax.axvline(0, color='red', linestyle='--', label='0% growth')
ax.set_title('Distribution of YoY Revenue-Proxy Growth')
ax.set_xlabel('YoY Growth (%)'); ax.set_ylabel('Frequency')
ax.legend()

# 3. Turnover trend (if available)
ax = axes[1, 0]
if 'Turnover_Cr' in annual.columns:
    for t in top_tickers[:4]:
        sub = annual[annual['Ticker'] == t]
        ax.bar(sub['Year'].astype(str) + '_' + t[:4], sub['Turnover_Cr'], alpha=0.7, label=t)
    ax.set_title('Annual Turnover (₹ Crores) — Revenue Proxy')
    ax.set_xlabel('Year_Ticker'); ax.set_ylabel('Turnover (Cr)')
    ax.legend(fontsize=8); ax.tick_params(axis='x', rotation=45)
else:
    ax.text(0.5, 0.5, 'Volume data not available', ha='center', va='center', transform=ax.transAxes)
    ax.set_title('Annual Turnover')

# 4. Revenue growth heatmap (year x ticker)
ax = axes[1, 1]
pivot = annual.pivot(index='Ticker', columns='Year', values='YoY_Growth_Pct')
pivot_top = pivot.loc[pivot.index.isin(top_tickers[:8])]
sns.heatmap(pivot_top, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
            linewidths=0.5, ax=ax, annot_kws={'size': 7})
ax.set_title('YoY Growth Heatmap (%) — Selected Tickers')
ax.set_xlabel('Year'); ax.set_ylabel('Ticker')

plt.tight_layout()
plt.savefig('revenue_earnings_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

print("\\n── Revenue & Earnings Summary Statistics ──")
print(annual.groupby('Year')['YoY_Growth_Pct'].describe().round(2))
"""))

# ── Cell 3: Profitability Analysis ────────────────────────────────────────
cells.append(new_markdown_cell("""---
## Cell 3 — Feature 2: Profitability Analysis

Profitability metrics derived from OHLCV:
- **Gross Margin proxy**: (Close - Low) / Close  — downside buffer
- **Operating Margin proxy**: (High - Low) / High  — trading range efficiency
- **Net Profit Margin proxy**: Daily return when positive
- **ROE proxy**: Annual return on avg price (earnings/book equivalent)
- **ROA proxy**: Sharpe-like ratio (mean return / std return)
"""))
cells.append(new_code_cell("""
# ── Profitability Analysis ──────────────────────────────────────────────
df2 = raw.copy().dropna(subset=['Date', 'Open', 'High', 'Low', 'Close'])
df2['Year'] = df2['Date'].dt.year

# Daily margin proxies
df2['Gross_Margin_Proxy']  = (df2['Close'] - df2['Low'])  / df2['Close'] * 100
df2['Op_Margin_Proxy']     = (df2['High']  - df2['Low'])  / df2['High']  * 100
df2['Daily_Return']        = df2.groupby('Ticker')['Close'].pct_change() * 100
df2['Net_Margin_Proxy']    = df2['Daily_Return'].clip(lower=0)   # positive-return days

# Annual aggregation
profit_annual = df2.groupby(['Ticker', 'Year']).agg(
    Gross_Margin = ('Gross_Margin_Proxy', 'mean'),
    Op_Margin    = ('Op_Margin_Proxy',    'mean'),
    Net_Margin   = ('Net_Margin_Proxy',   'mean'),
    Mean_Return  = ('Daily_Return',       'mean'),
    Std_Return   = ('Daily_Return',       'std'),
    Avg_Close    = ('Close',              'mean'),
).reset_index()

# ROE proxy: annual price appreciation / average price
profit_annual['ROE_Proxy'] = profit_annual.groupby('Ticker')['Avg_Close'].pct_change() * 100
# ROA proxy: Sharpe ratio (risk-adjusted return)
profit_annual['ROA_Proxy'] = (profit_annual['Mean_Return'] /
                               (profit_annual['Std_Return'] + 1e-9))

top_tickers = profit_annual.groupby('Ticker')['ROE_Proxy'].mean().dropna().nlargest(6).index.tolist()

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Profitability Analysis', fontsize=15, fontweight='bold')

# 1. Gross Margin trend
ax = axes[0, 0]
for t in top_tickers[:4]:
    sub = profit_annual[profit_annual['Ticker'] == t]
    ax.plot(sub['Year'], sub['Gross_Margin'], marker='o', label=t)
ax.set_title('Gross Margin Proxy (%) Over Time')
ax.set_xlabel('Year'); ax.set_ylabel('Gross Margin (%)'); ax.legend(fontsize=8)

# 2. Operating Margin trend
ax = axes[0, 1]
for t in top_tickers[:4]:
    sub = profit_annual[profit_annual['Ticker'] == t]
    ax.plot(sub['Year'], sub['Op_Margin'], marker='s', label=t)
ax.set_title('Operating Margin Proxy (%) Over Time')
ax.set_xlabel('Year'); ax.set_ylabel('Op Margin (%)'); ax.legend(fontsize=8)

# 3. Net Margin trend
ax = axes[0, 2]
for t in top_tickers[:4]:
    sub = profit_annual[profit_annual['Ticker'] == t]
    ax.plot(sub['Year'], sub['Net_Margin'], marker='^', label=t)
ax.set_title('Net Profit Margin Proxy (%) Over Time')
ax.set_xlabel('Year'); ax.set_ylabel('Net Margin (%)'); ax.legend(fontsize=8)

# 4. ROE proxy bar
ax = axes[1, 0]
roe_latest = profit_annual.groupby('Ticker')['ROE_Proxy'].mean().dropna().sort_values(ascending=False).head(10)
ax.barh(roe_latest.index, roe_latest.values, color='mediumseagreen')
ax.axvline(0, color='red', linestyle='--')
ax.set_title('Avg ROE Proxy (%) — Top 10 Tickers')
ax.set_xlabel('ROE Proxy (%)')

# 5. ROA proxy scatter
ax = axes[1, 1]
latest_year = profit_annual['Year'].max()
sub_latest = profit_annual[profit_annual['Year'] == latest_year].dropna(subset=['ROA_Proxy', 'ROE_Proxy'])
ax.scatter(sub_latest['ROA_Proxy'], sub_latest['ROE_Proxy'],
           alpha=0.6, edgecolors='white', s=60, c='steelblue')
ax.set_title(f'ROA vs ROE Proxy ({latest_year})')
ax.set_xlabel('ROA Proxy (Sharpe-like)'); ax.set_ylabel('ROE Proxy (%)')

# 6. Margin comparison — latest year
ax = axes[1, 2]
latest = profit_annual[profit_annual['Year'] == latest_year].copy()
latest = latest.set_index('Ticker')[['Gross_Margin', 'Op_Margin', 'Net_Margin']].head(10)
latest.plot(kind='bar', ax=ax, colormap='Set2')
ax.set_title(f'Margin Comparison ({latest_year}) — Sample Tickers')
ax.set_xlabel('Ticker'); ax.set_ylabel('Margin (%)'); ax.tick_params(axis='x', rotation=45)
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('profitability_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

print("\\n── Profitability Summary (Latest Year) ──")
print(latest.describe().round(2))
"""))

# ── Cell 4: Live Yahoo Finance API Integration ───────────────────────────
cells.append(new_markdown_cell("""---
## Cell 4 — Live API Integration: Yahoo Finance via Module 2 Backend

Connects to the FastAPI backend (`http://localhost:8000`) to pull live financial data
and runs the same revenue & profitability analysis on real-time data.

> **Prerequisite:** Start the backend first with:
> ```
> cd backend && venv\\Scripts\\uvicorn main:app --reload
> ```
"""))
cells.append(new_code_cell("""
import requests
import json
import joblib

BASE_URL = "http://localhost:8000/api"
TICKER   = "RELIANCE.NS"    # NSE ticker for Reliance Industries

# ── Fetch financials from Module 2 API ───────────────────────────────────
print(f"Fetching financials for {TICKER}...")
try:
    resp = requests.get(f"{BASE_URL}/stocks/financials/{TICKER}", timeout=30)
    resp.raise_for_status()
    financials = resp.json()
    
    print(f"Status: {resp.status_code}")
    print("Available keys:", list(financials.keys()) if isinstance(financials, dict) else "list")
    
    # Extract income statement data if available
    if isinstance(financials, dict):
        income_data = financials.get('income_statement') or financials.get('financials') or {}
        print("\\nSample financial data received:")
        if income_data:
            df_live = pd.DataFrame(income_data)
            print(df_live.head())
        else:
            print(json.dumps({k: str(v)[:100] for k, v in financials.items()}, indent=2))
            
except requests.exceptions.ConnectionError:
    print("⚠️ Backend not running. Start it with: cd backend && venv\\\\Scripts\\\\uvicorn main:app --reload")
    financials = {}
"""))

cells.append(new_code_cell("""
# ── Fetch profile + OHLCV for the same ticker ────────────────────────────
try:
    profile_resp = requests.get(f"{BASE_URL}/stocks/profile/{TICKER}", timeout=30)
    ohlcv_resp   = requests.get(f"{BASE_URL}/stocks/historical/{TICKER}?period=1y", timeout=30)
    
    if profile_resp.status_code == 200:
        profile = profile_resp.json()
        print("Company Profile:")
        for k in ['name', 'sector', 'industry', 'marketCap', 'trailingPE', 'priceToBook']:
            if k in profile:
                print(f"  {k}: {profile[k]}")
    
    if ohlcv_resp.status_code == 200:
        ohlcv_data = ohlcv_resp.json()
        ohlcv_list = ohlcv_data.get('data') or ohlcv_data if isinstance(ohlcv_data, list) else []
        if ohlcv_list:
            df_ohlcv = pd.DataFrame(ohlcv_list)
            if 'date' in df_ohlcv.columns:
                df_ohlcv['date'] = pd.to_datetime(df_ohlcv['date'])
                df_ohlcv = df_ohlcv.sort_values('date')
            print(f"\\nOHLCV rows: {len(df_ohlcv)}")
            print(df_ohlcv.tail(5))
            
            # Quick profitability analysis on live data
            if 'close' in df_ohlcv.columns:
                df_ohlcv['Daily_Return'] = df_ohlcv['close'].pct_change() * 100
                mean_ret = df_ohlcv['Daily_Return'].mean()
                std_ret  = df_ohlcv['Daily_Return'].std()
                sharpe   = mean_ret / (std_ret + 1e-9)
                total_ret = ((df_ohlcv['close'].iloc[-1] / df_ohlcv['close'].iloc[0]) - 1) * 100
                print(f"\\n── Live Profitability Metrics ({TICKER}) ──")
                print(f"  Mean Daily Return : {mean_ret:.4f}%")
                print(f"  Std Daily Return  : {std_ret:.4f}%")
                print(f"  Sharpe (ROA proxy): {sharpe:.4f}")
                print(f"  Total Return 1Y   : {total_ret:.2f}%")
                
except requests.exceptions.ConnectionError:
    print("⚠️ Backend not running.")
"""))

cells.append(new_code_cell("""
# ── Apply saved ML Model to live OHLCV data ──────────────────────────────
try:
    best_model  = joblib.load('best_model.pkl')
    scaler_obj  = joblib.load('scaler.pkl')
    feat_cols   = joblib.load('feature_columns.pkl')
    print("Loaded best_model.pkl, scaler.pkl, feature_columns.pkl ✓")
    
    # Rebuild features from live OHLCV
    if 'df_ohlcv' in dir() and len(df_ohlcv) > 30:
        ldf = df_ohlcv.copy()
        close_col = 'close' if 'close' in ldf.columns else 'Close'
        high_col  = 'high'  if 'high'  in ldf.columns else 'High'
        low_col   = 'low'   if 'low'   in ldf.columns else 'Low'
        vol_col   = 'volume' if 'volume' in ldf.columns else ('Volume' if 'Volume' in ldf.columns else None)
        
        ldf['Daily_Return']     = ldf[close_col].pct_change()
        ldf['Log_Return']       = np.log(ldf[close_col] / ldf[close_col].shift(1))
        ldf['Price_Range']      = ldf[high_col] - ldf[low_col]
        ldf['Price_Range_Pct']  = ldf['Price_Range'] / ldf[close_col]
        ldf['MA5']              = ldf[close_col].rolling(5).mean()
        ldf['MA20']             = ldf[close_col].rolling(20).mean()
        ldf['MA5_20_Cross']     = (ldf['MA5'] > ldf['MA20']).astype(int)
        
        def rsi(s, p=14):
            d = s.diff(); g = d.clip(lower=0).rolling(p).mean(); l = (-d.clip(upper=0)).rolling(p).mean()
            return 100 - 100/(1 + g/(l+1e-9))
        ldf['RSI14'] = rsi(ldf[close_col])
        
        if vol_col:
            ldf['Vol_MA5']  = ldf[vol_col].rolling(5).mean()
            ldf['Vol_Ratio'] = ldf[vol_col] / (ldf['Vol_MA5'] + 1)
        
        # Align to training features
        available_feats = [f for f in feat_cols if f in ldf.columns]
        X_live = ldf[available_feats].dropna()
        
        if len(X_live) > 0:
            X_live_sc = scaler_obj.transform(X_live[available_feats])
            predictions = best_model.predict(X_live_sc)
            probas = best_model.predict_proba(X_live_sc)[:, 1] if hasattr(best_model, 'predict_proba') else predictions
            
            last_pred  = predictions[-1]
            last_proba = probas[-1]
            direction  = "📈 UP" if last_pred == 1 else "📉 DOWN/FLAT"
            
            print(f"\\n── ML Prediction for {TICKER} ──")
            print(f"  Next-day direction : {direction}")
            print(f"  Confidence         : {last_proba:.2%}")
            print(f"  Features used      : {available_feats}")
        else:
            print("Not enough live data to build features.")
    else:
        print("Run the OHLCV fetch cell first (cell above).")
        
except FileNotFoundError:
    print("⚠️ Model files not found. Run 01_model_training.ipynb first.")
"""))

# ── Assemble ─────────────────────────────────────────────────────────────
nb.cells = cells
out_path = os.path.join(os.path.dirname(__file__), '02_features_analysis.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)
print(f"Written: {out_path}")
