# Multi-Agent Stock Research Analyst Platform
## Module 1: User Authentication and Research Workspace
## Module 2: Stock Search and Market Data Collection

An institutional-grade stock research workstation integrating **FastAPI**, **PostgreSQL** via **SQLAlchemy**, signed **JWT token authentication**, automated **Data Quality & Integrity Validation Engine**, multi-market stock data collection (**NSE**, **BSE**, **NASDAQ**, **NYSE**), Free API support (**Alpha Vantage**, **Twelve Data**), and a responsive **React.js + Tailwind CSS** frontend.

---

## 🌟 Platform Capabilities & Modules

### Module 1: User Authentication & Workspace
- **JWT Authentication Guard**: HMAC-SHA256 tokens with Bcrypt password hashing (12 rounds) and user-tied session dependencies.
- **Relational Watchlist**: Instant addition and removal of target stocks with database-level uniqueness enforcement per user (`user_id`, `ticker`).
- **Research Workspace & Preferences**: Persistent user preferences for preferred market (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and lookback period (`1M`, `3M`, `6M`, `1Y`, `5Y`).
- **Multi-Agent Research Pipeline**: Background dispatch of 5 autonomous agents (Fundamental, Technical, Sentiment, Risk Management, Lead Synthesizer) with consolidated audit reports.

### Module 2: Stock Search and Market Data Collection
- **Company Search**: Multi-market search by company name or ticker symbol across NSE, BSE, NASDAQ, and NYSE with real-time autocompletion.
- **Historical OHLCV Data Collection**: Ingestion of Open, High, Low, Close, and Volume time-series across configurable periods (`1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`).
- **Company Profiles & Financial Statements**:
  - Detailed company overview: CEO, sector, industry, employees, headquarters, market cap, P/E ratio, 52-week range, dividend yield, and beta.
  - Complete 3-statement financial models: **Income Statement**, **Balance Sheet**, and **Cash Flow Statement** with Annual and Quarterly views plus key financial ratios (ROE, ROA, Net Margin, Current Ratio, Debt-to-Equity).
- **Data Source & Retrieval Timestamp Tracking**: Strict provenance recording on every price feed and financial statement with ISO 8601 UTC timestamps and source attribution (`Alpha Vantage`, `Twelve Data`, `NSE Direct Exchange Feed`, `Calibrated Institutional Feed`).
- **Automated Data Quality & Validation Engine**:
  - **Missing Value Handling**: Automatic detection and imputation of missing or null prices and volumes.
  - **Duplicate Date Elimination**: Deduplication of colliding date timestamps.
  - **Inconsistent Data Correction**: Mathematical price bounds enforcement (`Low <= Open, Close <= High`), non-positive price repair, negative volume rectification, and chronological re-sorting.
  - **Quality Scoring**: Generation of an institutional Data Quality Index (0-100%) and audit log.
- **Free Market APIs for NYSE & NASDAQ**:
  - **Alpha Vantage**: Integrated REST endpoints for quotes, historical prices, overview profiles, and financial statements.
  - **Twelve Data**: Integrated REST client with support for up to 800 free requests/day.
  - **Calibrated Institutional Engine**: Zero-crash fallback guaranteeing continuous offline and rate-limit availability.


---

## 🗄️ Database Schema Design

The database schema is defined in [`backend/app/models.py`](file:///backend/app/models.py) with relational constraints and indexes:

### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | Integer | PK, Autoincrement, Index | Unique identifier |
| `full_name` | String(120) | NOT NULL | Analyst full name |
| `email` | String(255) | UNIQUE, Index, NOT NULL | Login credential |
| `password_hash` | String(255) | NOT NULL | Bcrypt salt & hashed password |
| `created_at` | DateTime | NOT NULL, UTC | Account timestamp |

### 2. `saved_stocks` (Watchlist)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `saved_stock_id` | Integer | PK, Autoincrement, Index | Watchlist entry identifier |
| `user_id` | Integer | FK (`users.user_id`, CASCADE), Index | Owner user ID |
| `ticker` | String(20) | Index, NOT NULL | Stock symbol (e.g. RELIANCE, TCS) |
| `created_at` | DateTime | NOT NULL, UTC | Added timestamp |
* **Constraint**: `UniqueConstraint("user_id", "ticker")` prevents duplicate ticker entries for the same user.

### 3. `research_tasks`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `task_id` | Integer | PK, Autoincrement, Index | Task identifier |
| `user_id` | Integer | FK (`users.user_id`, CASCADE), Index | Task owner |
| `ticker` | String(20) | Index, NOT NULL | Equity evaluated |
| `market` | String(20) | NOT NULL, Default 'NSE' | NSE, BSE, NASDAQ, NYSE |
| `requested_period` | String(30) | NOT NULL, Default '6 Months'| Lookback timeframe |
| `status` | String(20) | NOT NULL | Pending, Processing, Completed, Failed |
| `summary` | Text | Nullable | Synthesis of agent findings |
| `recommendation` | String(20) | Nullable | Strong Buy, Buy, Hold, Sell |
| `target_price` | String(50) | Nullable | Price target or upside percentage |
| `report_json` | Text | Nullable | Detailed JSON audit across all 4 agents |
| `created_at` | DateTime | NOT NULL, UTC | Dispatched timestamp |
| `completed_at` | DateTime | Nullable | Finalized timestamp |

### 4. `user_preferences`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `preference_id` | Integer | PK, Autoincrement | Preference identifier |
| `user_id` | Integer | FK (`users.user_id`, CASCADE), UNIQUE | 1:1 linked user |
| `preferred_market` | String(20) | Default 'NSE' | NSE, BSE, NASDAQ, NYSE |
| `preferred_analysis_period` | String(30) | Default '6 Months'| 1M, 3M, 6M, 1Y, 5Y |
| `updated_at` | DateTime | NOT NULL, UTC | Last modification timestamp |

### 5. `market_data_records` (Module 2)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, Autoincrement | Record identifier |
| `ticker` | String(20) | Index, NOT NULL | Stock symbol |
| `market` | String(20) | Index, NOT NULL | NSE, BSE, NASDAQ, NYSE |
| `record_date` | String(30) | Index, NOT NULL | Calendar trade date |
| `open_price` | Float | NOT NULL | Open price |
| `high_price` | Float | NOT NULL | High price |
| `low_price` | Float | NOT NULL | Low price |
| `close_price` | Float | NOT NULL | Close price |
| `volume` | Integer | NOT NULL | Traded volume |
| `data_source` | String(100) | NOT NULL | Alpha Vantage, Twelve Data, NSE Direct, etc. |
| `retrieved_at` | DateTime | NOT NULL, UTC | Ingestion timestamp |

### 6. `company_profiles` (Module 2)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `profile_id` | Integer | PK, Autoincrement | Profile identifier |
| `ticker` | String(20) | Index, NOT NULL | Stock symbol |
| `market` | String(20) | Index, NOT NULL | Market exchange |
| `company_name` | String(150) | NOT NULL | Full corporate legal name |
| `sector` | String(100) | Nullable | Primary business sector |
| `ceo` | String(100) | Nullable | Executive leadership |
| `market_cap` | String(50) | Nullable | Total capitalization |
| `pe_ratio` | Float | Nullable | Price to Earnings |
| `week_52_high` | Float | Nullable | 52-week highest close |
| `week_52_low` | Float | Nullable | 52-week lowest close |
| `data_source` | String(100) | NOT NULL | Feed attribution |
| `retrieved_at` | DateTime | NOT NULL, UTC | Ingestion timestamp |

### 7. `company_financials` (Module 2)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `financial_id` | Integer | PK, Autoincrement | Financial record identifier |
| `ticker` | String(20) | Index, NOT NULL | Stock symbol |
| `market` | String(20) | Index, NOT NULL | Market exchange |
| `period_type` | String(20) | NOT NULL | 'annual' or 'quarterly' |
| `data_json` | Text | NOT NULL | JSON 3-statement model & ratios |
| `data_source` | String(100) | NOT NULL | Regulatory filings feed |
| `retrieved_at` | DateTime | NOT NULL, UTC | Ingestion timestamp |

### 8. `data_validation_logs` (Module 2)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `log_id` | Integer | PK, Autoincrement | Audit log identifier |
| `ticker` | String(20) | Index, NOT NULL | Evaluated ticker |
| `total_records` | Integer | NOT NULL | Raw input count |
| `clean_records` | Integer | NOT NULL | Clean output count |
| `missing_values_handled`| Integer | NOT NULL | Imputed missing prices/volumes |
| `duplicate_dates_removed`| Integer | NOT NULL | Deduplicated collisions |
| `inconsistencies_corrected`| Integer | NOT NULL | Price bounds & negative volumes repaired |
| `quality_score` | Float | NOT NULL | Mathematical data quality index (0-100%) |
| `issues_json` | Text | Nullable | Serialized issues audit trail |
| `validated_at` | DateTime | NOT NULL, UTC | Audit timestamp |


---

## 🔒 Security & Authentication Specification

1. **Password Hashing**: Stored passwords use `bcrypt` salt rounds (12). Plaintext passwords are never stored or logged.
2. **JWT Tokens**:
   - Algorithm: `HS256`
   - Payload: `{"sub": "<user_id>", "user_id": <user_id>, "exp": <timestamp>, "iat": <timestamp>}`
   - Expiry: 24 Hours
3. **Route Authorization Guard**:
   - Protected endpoints require `Authorization: Bearer <token>`
   - Dependency `get_current_user` in [`backend/app/dependencies.py`](file:///backend/app/dependencies.py) decodes token, validates expiration/signature, and strictly queries the user from DB.
   - **Critical Rule**: Client payload cannot override `user_id`; `user_id` is always derived strictly from the verified JWT.

---

## 📡 REST API Endpoints Catalog

Base prefix: `/api/v1`

### Authentication (`/api/v1`)
- `POST /register`: Create a new user (Full Name, Email, Password)
- `POST /login`: Authenticate credentials, return signed JWT
- `GET /me`: Get authenticated user profile (`Bearer <token>`)

### Watchlist (`/api/v1/watchlist`)
- `GET /watchlist`: Retrieve user's saved stocks
- `POST /watchlist`: Add stock ticker (duplicates prevented per user)
- `DELETE /watchlist/{ticker}`: Remove ticker from user watchlist

### Research History & Tasks (`/api/v1`)
- `GET /history`: Retrieve user's past research tasks
- `POST /tasks`: Dispatch a multi-agent research task for a ticker
- `GET /tasks/{task_id}`: Retrieve detailed multi-agent report

### Preferences (`/api/v1/preferences`)
- `GET /preferences`: Retrieve market and analysis period preferences
- `PUT /preferences`: Update preferred market and analysis period

### Market Intelligence & Data Collection (`/api/v1/market`) [Module 2]
- `GET /market/search?query={q}&market={market}`: Search companies across NSE, BSE, NASDAQ, NYSE by name or ticker
- `GET /market/historical/{ticker}?market={mkt}&period={period}`: Retrieve historical OHLCV data + validation report + source + UTC timestamp
- `GET /market/profile/{ticker}?market={mkt}`: Retrieve comprehensive company profile & valuation multiples
- `GET /market/financials/{ticker}?market={mkt}&period_type={annual|quarterly}`: Retrieve 3-statement model (Income, Balance Sheet, Cash Flow) & financial ratios
- `POST /market/validate`: Standalone Data Validation Engine for arbitrary datasets (detects/repairs missing values, duplicate dates, price bounds)
- `GET /market/quote/{ticker}?market={mkt}`: Real-time price quote with day range, volume, source, and timestamp
- `GET /market/status`: Check connection status & active providers (Alpha Vantage, Twelve Data, NSE/BSE)
- `POST /market/config`: Update and test custom Alpha Vantage and Twelve Data API keys

---

## 🚀 Quick Start Guide

### 1. Run Complete Platform Verification (Modules 1 & 2)
Verify all 10 platform phases, authentication, database schemas, stock search, OHLCV collection, automated validation engine, company profiles, and financial statements:
```powershell
$env:PYTHONPATH = "$PWD\backend"
.\backend\venv\Scripts\python.exe .\test_and_run_all.py
```

### 2. Run Dedicated Module 2 Test Suite
```powershell
$env:PYTHONPATH = "$PWD\backend"
.\backend\venv\Scripts\python.exe .\backend\test_market_data.py
```

### 3. Run Module 1 Direct Tests
```powershell
$env:PYTHONPATH = "$PWD\backend"
.\backend\venv\Scripts\python.exe .\backend\test_direct.py
```

### 4. Start the FastAPI Backend
```powershell
# Using the startup script:
.\start_backend.bat
# Or via powershell:
.\start_backend.ps1
```
Backend will be available at: **http://127.0.0.1:8000**
Interactive API Swagger Docs: **http://127.0.0.1:8000/docs**

### 5. Start the React Frontend
```powershell
# Using the startup script:
.\start_frontend.bat
# Or via powershell:
.\start_frontend.ps1
```
Frontend will be available at: **http://localhost:5173**


---

## ⚙️ PostgreSQL Configuration

To connect to your existing PostgreSQL server:
1. Update `DATABASE_URL` in `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/stock_research
   ```
2. Run database initialization:
   ```powershell
   $env:PYTHONPATH = "$PWD\backend"
   .\backend\venv\Scripts\python.exe .\backend\init_db.py
   ```
*(Note: If PostgreSQL is offline or inaccessible, the application automatically falls back to local SQLite database `stock_research.db` without crashing).*

