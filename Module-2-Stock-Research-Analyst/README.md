# Multi-Agent Stock Research Analyst
## Module 1: User Authentication and Research Workspace
## Module 2: Stock Search and Market Data Collection

### Overview
This repository contains the full end-to-end implementation for **Module 1 (User Authentication and Research Workspace)** and **Module 2 (Stock Search and Market Data Collection)** of the Multi-Agent Stock Research Analyst platform.

Built with a modern financial terminal aesthetic (**Dark Emerald & Charcoal**), the application integrates a high-performance **FastAPI (Python 3.11)** backend with **PostgreSQL**, an asynchronous data retrieval pipeline, and an interactive **React 18 + Vite + Tailwind CSS** frontend.

---

## 1. Project Requirements & Feature Matrix

| Module | Requirement | Status | Implementation Details |
|---|---|---|---|
| **M1** | **User Registration & Login** | ✅ Completed | Passwords securely hashed with `bcrypt` (gensalt rounds). Full Zod (frontend) & Pydantic (backend) validation. |
| **M1** | **JWT Authentication** | ✅ Completed | Stateless HS256 JWT tokens with `Authorization: Bearer <token>` interceptors and HTTP-only cookie support. |
| **M1** | **Google OAuth Sign-In** | ✅ Completed | Configured with Google Cloud Client ID (`282371573288-...apps.googleusercontent.com`). Verifies ID tokens via Google's tokeninfo API. |
| **M1** | **User-Specific Research History** | ✅ Completed | Strict isolation (`WHERE user_id = current_user.id`). Displays status badges (`Pending`, `Processing`, `Completed`, `Failed`). |
| **M1** | **Saved Stocks & Watchlists** | ✅ Completed | Bookmark target equities, inspect OHLCV charts, launch 1-click research, and prevent duplicate insertions. |
| **M1** | **User Preferences** | ✅ Completed | Persist default market exchanges (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and analysis horizons (`1 Month` to `5 Years`). |
| **M1** | **PostgreSQL Relational Schema** | ✅ Completed | Fully modeled with SQLAlchemy 2.0 (asyncio) + `asyncpg`. Foreign keys, unique constraints, and indexes. |
| **M2** | **1. Search Companies by Name / Ticker** | ✅ Completed | Real-time debounced search across US & Indian markets (`GET /api/stocks/search`). Queries live exchange endpoints with fallback cache. |
| **M2** | **2. Retrieve Historical Stock Prices** | ✅ Completed | Time-series endpoints (`GET /api/stocks/history/{ticker}`) with interactive SVG price-vs-time curves and hover inspection. |
| **M2** | **3. Collect OHLCV Data** | ✅ Completed | Candlestick data engine (`GET /api/stocks/ohlcv/{ticker}`) and database persistence (`POST /api/stocks/ohlcv/collect`). Exportable to CSV. |
| **M2** | **4. Company Profiles & Financials** | ✅ Completed | Corporate profiles, key executives, valuation metrics, multi-period Income Statements, Balance Sheets, and Cash Flow Statements. |
| **M2** | **5. Record Sources & Timestamps** | ✅ Completed | Immutable data provenance audit logs saved to PostgreSQL (`data_retrieval_audit_logs`) and displayed with live badges. |
| **M2** | **6. Data Quality & Quantitative Validation** | ✅ Completed | Automated engine detects missing values (imputed), duplicate dates (deduplicated), and price bounds ($High \ge Open/Close \ge Low$). |
| **M2** | **7. Supported Markets (NSE/BSE & NASDAQ/NYSE)**| ✅ Completed | 1-click market switcher. Automatically adapts trading hours, benchmark indices (NIFTY 50, SENSEX, NDX 100, S&P 500), and currency (₹ vs $). |

---

## 2. Key Architecture & Features

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

## 3. Technology Stack

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

## 4. PostgreSQL Relational Schema

```sql
-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Research Tasks Table
CREATE TABLE research_tasks (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(50) NOT NULL,
    market VARCHAR(50) NOT NULL,
    analysis_period VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Processing', 'Completed', 'Failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Research Reports Table
CREATE TABLE research_reports (
    id SERIAL PRIMARY KEY,
    task_id INT REFERENCES research_tasks(id) ON DELETE CASCADE,
    report_content TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Saved Stocks (Watchlist) Table
CREATE TABLE saved_stocks (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(50) NOT NULL,
    company_name VARCHAR(255),
    market VARCHAR(50),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);

-- 5. User Preferences Table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    market VARCHAR(50) DEFAULT 'NASDAQ',
    analysis_period VARCHAR(50) DEFAULT '1 Year',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Stock OHLCV Market Data Table
CREATE TABLE stock_ohlcv (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(50) NOT NULL,
    company_name VARCHAR(255),
    market VARCHAR(50),
    period VARCHAR(20),
    interval VARCHAR(20) NOT NULL DEFAULT '1d',
    timestamp BIGINT NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume BIGINT NOT NULL,
    source VARCHAR(100) NOT NULL DEFAULT 'Yahoo Finance',
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_stock_ohlcv_ticker_interval_timestamp UNIQUE (ticker, interval, timestamp)
);

-- 7. Company Financials & Profiles Table
CREATE TABLE company_financials_profiles (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    market VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    profile_data JSON,
    financials_data JSON,
    data_source VARCHAR(100) NOT NULL DEFAULT 'Yahoo Finance',
    retrieval_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Data Retrieval Provenance Audit Logs Table
CREATE TABLE data_retrieval_audit_logs (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_source VARCHAR(100) NOT NULL DEFAULT 'Yahoo Finance',
    status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    record_count INT NOT NULL DEFAULT 1,
    retrieval_timestamp TIMESTAMPTZ NOT NULL,
    metadata_info JSON,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. REST API Endpoints Reference

### Authentication & User Endpoints
- `POST /api/auth/register` — Register a new analyst account with encrypted password.
- `POST /api/auth/login` — Sign in with email and password, receives signed JWT.
- `POST /api/auth/google/login` — Sign in with Google ID token.
- `GET /api/auth/me` — Retrieve the currently authenticated user session.
- `POST /api/auth/logout` — Invalidate user session and clear auth cookies.

### Research Tasks & Automated Reports
- `GET /api/research/tasks` — List all research tasks for the authenticated user.
- `POST /api/research/tasks` — Create a new research task (auto-triggers background processing).
- `GET /api/research/tasks/{task_id}` — Get single research task details.
- `PATCH /api/research/tasks/{task_id}/status` — Update task status (`Pending`, `Processing`, `Completed`, `Failed`).
- `GET /api/research/tasks/{task_id}/report` — Retrieve the generated Markdown research report.

### Watchlists & Preferences
- `GET /api/watchlist` — Retrieve saved stocks in user watchlist.
- `POST /api/watchlist` — Add a stock to watchlist (`{ ticker, company_name, market }`).
- `DELETE /api/watchlist/{id}` — Remove a stock from watchlist.
- `GET /api/preferences` — Get user default market and timeframe preferences.
- `PUT /api/preferences` — Upsert user preferences.

### Stock Search & Market Data (Module 2)
- `GET /api/stocks/markets` — List all 4 supported markets (`NSE`, `BSE`, `NASDAQ`, `NYSE`) with metadata.
- `GET /api/stocks/markets/{market_code}` — Specific market details and trading hours.
- `GET /api/stocks/markets/{market_code}/stocks` — Popular benchmark equities for a market.
- `GET /api/stocks/search?q={query}&market={market}` — Search companies by name or ticker.
- `GET /api/stocks/quote/{ticker}` — Real-time price quote, day change, and volume.
- `GET /api/stocks/history/{ticker}?period={period}&interval={interval}` — Historical price time-series.
- `GET /api/stocks/ohlcv/{ticker}?period={period}&interval={interval}` — Validated OHLCV data points with data integrity report.
- `POST /api/stocks/ohlcv/collect` — Persist OHLCV candles to PostgreSQL.
- `GET /api/stocks/profile/{ticker}` — Comprehensive corporate profile, leadership, and valuation ratios.
- `GET /api/stocks/financials/{ticker}` — Multi-period Income Statements, Balance Sheets, and Cash Flow Statements.
- `GET /api/stocks/audit-logs?ticker={ticker}&limit={limit}` — Chronological data provenance audit logs.

