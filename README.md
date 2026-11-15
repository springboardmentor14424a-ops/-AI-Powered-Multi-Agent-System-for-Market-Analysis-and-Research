# Multi-Agent Stock Research Analyst — Module 1
## User Authentication and Research Workspace

### Overview
This project completes **Module 1: User Authentication and Research Workspace** for the Multi-Agent Stock Research Analyst platform. It implements all requirements: user registration with bcrypt hashing, JWT-based login (with HTTP-only cookie + Bearer token), Google OAuth authentication, personal research history, a live watchlist with Yahoo Finance stock search, user preferences management, and a PostgreSQL database schema.

The user interface is designed with a **Dark Green (Emerald/Slate)** financial terminal aesthetic.

---

## 1. What was to be done & Why

| Requirement | Purpose / Why it is needed |
|---|---|
| **1. User Registration** | Allows new research analysts to securely create an account. Passwords must never be stored in plain text. |
| **2. User Login** | Verifies credentials against stored bcrypt hashes and prevents unauthorized access to research data. |
| **3. JWT Authentication** | Enables stateless, secure session authorization across API requests without exposing credentials or user IDs. |
| **4. Research History** | Persists user-specific research tasks (company, ticker, market, period, status) and reports for auditability. |
| **5. Watchlists & Saved Stocks** | Enables tracking high-interest stocks with live quote lookups, adding/removing stocks, and 1-click research. |
| **6. User Preferences** | Lets users set default market exchanges (NSE, BSE, NASDAQ, NYSE) and timeframes (1M to 5Y). |
| **7. PostgreSQL Schema** | Persistent relational database enforcing primary keys, foreign keys, unique constraints, and indexes. |
| **Google Sign-In** | Modern passwordless authentication for ease of onboarding. |
| **Yahoo Finance Dataset** | Real-time market prices, company names, and financial metrics instead of static dummy values. |
| **Dark Green Aesthetic** | Financial terminal look & feel (Emerald green on deep charcoal). |

---

## 2. What is Done & How it Works

### A. Authentication & Security
- **Registration (`/api/auth/register`)**: Validates name, unique email, and minimum 8-character password. Confirms password matching using Zod (frontend) and Pydantic (backend). Hashes password via `bcrypt` (gensalt).
- **Standard Login (`/api/auth/login`)**: Verifies password hash using `bcrypt.checkpw()`. Generates signed HS256 JWT containing `sub: user_id` and expiration. Sets `access_token` as an HTTP-only cookie and returns it in the JSON body.
- **Google OAuth Login (`/api/auth/google/login`)**: Front-end uses `@react-oauth/google`. The backend validates the Google credential token with Google's tokeninfo API via `httpx`, finds or automatically provisions the user, and signs a JWT session.
- **Current User Dependency (`get_current_user`)**: FastAPI dependency inspects both the `Authorization: Bearer <token>` header and HTTP-only cookie, decodes the token, and attaches the authenticated `User` record to protected routes.

### B. Workspace & Research History
- **Research Tasks (`/api/research/tasks`)**: CRUD endpoints ensuring strict user isolation (`WHERE user_id = current_user.id`). Displays status badges (`Pending`, `Processing`, `Completed`, `Failed`).
- **New Task Modal**: Allows initiating new stock research with custom company name, ticker, exchange market, and period.

### C. Live Watchlist & Market Search (Yahoo Finance)
- **Live Search (`/api/stocks/search?q=...&market=...`)**: Real-time queries to Yahoo Finance for current price, currency, company name, and sector with instant fallback for rate limits.
- **Stock Quotes (`/api/stocks/quote/{ticker}`)**: Fetches real-time market price, day change, volume, P/E ratio, and market cap.
- **Watchlist CRUD (`/api/watchlist`)**: Add stocks, view saved symbols with live quotes, remove from watchlist, or launch research directly.

### D. Preferences
- **User Preferences (`/api/preferences`)**: Reads and upserts the default market (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and analysis period (`1 Month` to `5 Years`).

---

## 3. Technology Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS 3 (Dark green / Emerald theme)
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
- **HTTP Client**: `httpx` (Google token verification)
- **Market Data**: `yfinance` & Yahoo Finance Chart API
- **Data Validation**: Pydantic v2 + `pydantic-settings`

### Database
- **Database Engine**: PostgreSQL 13+
- **Schema Tables**: `users`, `research_tasks`, `research_reports`, `saved_stocks`, `user_preferences`

---

## 4. Database Schema Structure

```sql
-- Users (supports standard password and Google OAuth)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research Tasks
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

-- Saved Stocks (Watchlist)
CREATE TABLE saved_stocks (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(50) NOT NULL,
    company_name VARCHAR(255),
    market VARCHAR(50),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);

-- User Preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    market VARCHAR(50) DEFAULT 'NASDAQ',
    analysis_period VARCHAR(50) DEFAULT '1 Year',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Project Verification & Results

- **Registration & Login**: Verified with password hashing, error feedback, and JWT session handling.
- **Google OAuth**: Button integrated on login page.
- **Stock Search & Live Data**: Live queries for tickers like `AAPL`, `MSFT`, `TSLA`, `RELIANCE`, `TCS` return current prices and metrics from Yahoo Finance.
- **Watchlist**: Adding/removing saved stocks functions with instantaneous state update.
- **Preferences**: Allows switching between default exchanges and periods, persisted in PostgreSQL.
- **Build Status**: Production frontend build compiles cleanly (`npm run build` succeeds). Backend imports and dependencies verified.

