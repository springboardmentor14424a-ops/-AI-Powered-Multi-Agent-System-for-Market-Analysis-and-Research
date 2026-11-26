# Multi-Agent Stock Research Analyst
## Module 1: User Authentication and Research Workspace
## Module 2: Stock Search and Market Data Collection
## Module 3: Fundamental Analysis Agent (ML Modeling & Feature Engineering)

## Overview

The **Multi-Agent Stock Research Analyst** is a full-stack equity research and quantitative analysis platform built with **React 18**, **FastAPI**, **PostgreSQL**, and **XGBoost**. It brings together secure user workspace management, multi-market data ingestion across Indian (`NSE`, `BSE`) and US (`NASDAQ`, `NYSE`) exchanges, and an ML-backed Fundamental Analysis Agent into a unified financial terminal UI.

The platform is organized into three integrated modules:

- **Module 1 — User Authentication and Research Workspace**: Provides `bcrypt` + HS256 JWT authentication and Google OAuth sign-in alongside a PostgreSQL-backed workspace (`Research History`, `Watchlist`, and `Preferences`) with asynchronous background task execution that generates and persists Markdown stock research reports.
- **Module 2 — Stock Search and Market Data Collection**: Integrates live Yahoo Finance market APIs (with fallback support) for ticker search, quotes, company profiles, financial statements, and interactive OHLCV charting (`Stock Search & OHLCV`), backed by an automated OHLCV validation engine (`_validate_ohlcv_dataset`) and PostgreSQL audit logging (`data_retrieval_audit_logs`).
- **Module 3 — Fundamental Analysis Agent (ML Modeling & Feature Engineering)**: Combines Module 2 market/financial feeds (with `archive_data/` fallback) and a serialized **XGBoost** classifier (achieving **94.21% accuracy** across 7 benchmarked models on 74,518 cleaned sessions from 98 NIFTY equities) via `/api/agent/fundamental/{ticker}` and the `Agent` dashboard tab to deliver revenue and earnings checks, 3-tier profitability classification, debt/stability scoring, `P/E`, `P/B`, and `ROE` ratio analysis, historical performance comparisons, peer benchmarking, anomaly detection, and data-quality audits, documented alongside reproducible Jupyter notebooks in `notebooks/`.

---

## 1. Key Architecture & Features

### A. Authentication & Security (Module 1)
- **Standard Registration & Login (`/api/auth/register`, `/api/auth/login`)**:
  - Passwords are encrypted using `bcrypt.hashpw` with per-user salt rounds. Raw passwords are never stored.
  - Upon successful credentials verification, an HS256-signed JWT token is returned containing the user ID and expiration time.
- **Google OAuth Integration (`/api/auth/google/login`)**:
  - Supports live Google Sign-In with configured Google Cloud Client ID (`VITE_GOOGLE_CLIENT_ID`).
  - The backend verifies Google ID tokens via `https://oauth2.googleapis.com/tokeninfo`, creates or links the Google user profile in PostgreSQL, and generates an authorized session token.
- **Current User Dependency (`get_current_user`)**:
  - FastAPI dependency verifies JWT headers (`Authorization: Bearer <token>`) and provides authenticated user injection with strict row-level isolation.

### B. Autonomous Research Engine & Report Generation
- **Asynchronous Task Processing**:
  - Initiating research tasks triggers a background worker:
    $$\text{Pending} \longrightarrow \text{Processing} \longrightarrow \text{Completed}$$
  - Collects historical price trends, corporate summaries, financial statements, and valuation multiples.
  - Compiles an institutional-grade Markdown research report saved to the PostgreSQL `research_reports` table.
- **Interactive Report Viewer**:
  - Clicking **View Report** in the Research History tab opens an interactive modal displaying:
    - 📊 **Price Movement Analytics**: Current price, period net change, 52-week boundaries, and daily trading volume.
    - 🏢 **Company Profile**: Business summary, sector, industry classification, employee count, and headquarters.
    - 💰 **Financial Health Metrics**: Revenue, gross margins, operating margins, profit margins, and return on equity (ROE).
    - 📈 **Valuation Multiples**: Trailing P/E, Forward P/E, PEG Ratio, Price-to-Book, EV/EBITDA, and Beta.

### C. Live Market Data & Interactive Stock Charting (Module 2)
- **Interactive SVG Charting**:
  - Responsive price-vs-time curve with volume bars, customizable timeframes (`1D`, `5D`, `1M`, `3M`, `6M`, `1Y`, `5Y`), and intervals (`5 Min`, `Daily`, `Weekly`).
  - Interactive mouse inspection displays high, low, open, close, date, and volume at any coordinate.
- **Quantitative Data Validation Engine (`_validate_ohlcv_dataset`)**:
  - **Missing Values**: Detects missing or NaN prices/volumes; forward-fills and imputes gaps.
  - **Duplicate Dates**: Deduplicates repeated timestamps to guarantee chronological uniqueness.
  - **Inconsistent Bounds**: Validates $High \ge Low$ and ensures Open/Close remain strictly inside $[Low, High]$. Enforces non-negative price and volume constraints.
  - **Data Integrity Score**: Emits a 100% data integrity score banner directly in the user interface.
- **Multi-Market Support (India & US)**:
  - 1-click market switcher for `NSE`, `BSE`, `NASDAQ`, and `NYSE`.
  - Dynamically formats monetary figures in **₹ INR** (Lakh/Crore) for Indian stocks and **$ USD** (Millions/Billions) for US equities.
  - Provides quick-select benchmark equity buttons (e.g. `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `AAPL`, `MSFT`, `NVDA`).
- **Data Provenance & Audit Trail**:
  - Every API response attaches its exact `data_source` and ISO 8601 UTC `retrieval_timestamp`.
  - All operations are permanently written to PostgreSQL (`data_retrieval_audit_logs`) and accessible via the **Data Sources & Audit Logs** viewer.

---

## 2. Technology Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS 3 (Dark green / Emerald financial terminal theme)
- **Routing**: React Router v6
- **Forms & Validation**: React Hook Form + Zod
- **HTTP Client**: Axios with Bearer request interceptors and 401 redirect handling
- **OAuth**: `@react-oauth/google`
- **UI Components & Icons**: `lucide-react`, `react-hot-toast`

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ASGI Server**: Uvicorn
- **ORM / Driver**: SQLAlchemy 2.0 (asyncio) + `asyncpg` + `psycopg2-binary`
- **Authentication**: `python-jose` (HS256 JWT), `bcrypt` (password hashing)
- **HTTP Client**: `httpx` (Google token verification and live market API calls)
- **Market Data**: Direct Yahoo Finance HTTP Chart & Search APIs with fallback datasets
- **Data Validation**: Pydantic v2 + `pydantic-settings`

### Database
- **Database Engine**: PostgreSQL 13+
- **Schema Tables**: `users`, `research_tasks`, `research_reports`, `saved_stocks`, `user_preferences`, `stock_ohlcv`, `company_financials_profiles`, `data_retrieval_audit_logs`

---

## 4. Module 3: Fundamental Analysis Agent & Machine Learning Report

### A. Dataset Preprocessing & Data Validation
Using the extensive stock dataset extracted from `archive.zip` (98 NIFTY equities across multiple years):
1. **Missing Value Validation**: Identified and imputed sparse columns (e.g., `Trades` missing in 12.56% of historical records) while retaining core price/volume integrity.
2. **Duplicate Dates Validation**: Detected and resolved 162 duplicate (Symbol, Date) records.
3. **Inconsistent Data Validation**:
   - Zero violations for $High < Low$ bounds.
   - Zero violations for non-positive ($Price \le 0$) values.
   - Cleaned dataset finalized at **74,518 verified trading sessions**.

### B. Feature Engineering & 80/20 Train-Test Split
- **Dataset Partitioning**: 80% Training ($59,102$ samples) and 20% Testing ($14,776$ samples), stratified across market regimes.
- **Engineered Features (12)**:
  - Momentum & Returns: `Daily_Return`, `Return_5D`, `Return_20D`
  - Volatility & Risk: `Volatility_20D` (20-day rolling standard deviation)
  - Intraday Liquidity: `Spread` ($(High - Low) / Close$)
  - Institutional Strength: `Deliv_Pct` (Delivery volume ratio)
  - Capital Throughput: `Turnover_Cr` (Turnover in ₹ Crores)
  - Technical Oscillators: `RSI_14`, `MACD`, `MACD_Signal`, `MACD_Hist`
  - Volume Accumulation: `Vol_Surge` ($Volume / Volume_{MA20}$)

### C. Machine Learning Benchmark & Model Comparison Report

> **Requirement**: Best model must achieve **> 90% accuracy**.  
> **Result**: **XGBoost achieved 94.21% Accuracy, 0.9494 F1-Score, and 0.9860 ROC-AUC**, successfully exceeding all requirements.

| Rank | Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Status |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **XGBoost (Selected Best)** | **94.21%** | **94.74%** | **95.14%** | **0.9494** | **0.9860** | **Exceeds Target (>90%)** |
| 🥈 | **LightGBM** | 94.10% | 94.65% | 95.03% | 0.9484 | 0.9852 | Exceeds Target (>90%) |
| 🥉 | **Gradient Boosting** | 93.99% | 94.57% | 94.93% | 0.9475 | 0.9844 | Exceeds Target (>90%) |
| 4 | **Random Forest** | 93.92% | 94.46% | 94.92% | 0.9469 | 0.9834 | Exceeds Target (>90%) |
| 5 | **Logistic Regression** | 92.14% | 92.25% | 94.13% | 0.9318 | 0.9686 | Exceeds Target (>90%) |
| 6 | **Decision Tree** | 91.88% | 92.92% | 92.85% | 0.9289 | 0.9267 | Exceeds Target (>90%) |
| 7 | **K-Nearest Neighbors** | 78.09% | 79.12% | 83.72% | 0.8135 | 0.8600 | Baseline |

### D. Jupyter Notebooks Deliverables

1. **`notebooks/01_model_training.ipynb`**:
   - Data validation (missing values, duplicate dates, price inconsistencies)
   - Preprocessing & 12 feature transformations
   - 80/20 train/test split
   - Model development across 7 ML algorithms
   - Full evaluation comparison table & metric visualization charts
   - Confusion matrix & classification report
   - Model artifact serialization (`best_model.pkl`, `scaler.pkl`, `feature_columns.pkl`)

2. **`notebooks/02_features_analysis.ipynb`** (Each feature in its own dedicated cell):
   - **Cell 1**: Full 98-stock dataset ingestion & sector classification across 9 sectors.
   - **Cell 2 [Feature 1]**: **Revenue & Earnings Analysis** (YoY revenue growth curves, earnings proxies, turnover analysis, growth distributions, and correlation heatmaps).
   - **Cell 3 [Feature 2]**: **Profitability Analysis (3-Tier Range)** (Gross/Operating/Net margins, ROE, ROA, classified into **Highly Profitable**, **Moderately Profitable**, and **Not Profitable**).
   - **Cell 4 [Feature 3]**: **Debt and Financial Stability Analysis** (Total debt, Debt-to-Equity (D/E), Debt-to-Assets (D/A), solvency buffer %, Interest Coverage, and Financial Stability Index rankings).
   - **Cell 5 [Feature 4]**: **Calculation of Financial Ratios (P/E, P/B, ROE)** (Coherent valuation multiples when data is available, P/B vs ROE matrix, negative-earnings N/A handling, and valuation bands).
   - **Cell 6 [Feature 5]**: **Historical Financial Performance Comparison** (Year-by-year progression table, normalized cumulative growth curves, 3-Year vs 5-Year CAGR comparison, and risk-return vs drawdown profiles).
   - **Cell 7 [Feature 6]**: **Peer Comparison (Where Comparable Data is Available)** (Sector peer grouping across IT Services & Energy, Target vs Peer Average benchmarking, and incomplete-peer exclusion handling).
   - **Cell 8 [Feature 7]**: **Identification of Missing or Inconsistent Financial Information** (Missing values audit across 98 stocks, duplicate date detection, OHLC/Volume bound checks, unadjusted split outlier alerts, and Data Reliability Score).
   - **Cell 9 [Live API Integration]**: Connects directly with the Module 2/3 FastAPI Yahoo Finance bridge, loads `best_model.pkl` (94.21% XGBoost), runs all 7 features, and outputs complete Fundamental Analysis Agent demo reports.


