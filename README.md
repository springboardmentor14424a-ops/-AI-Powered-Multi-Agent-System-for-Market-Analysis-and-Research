# Multi-Agent Stock Research Analyst Platform
## Module 1: User Authentication and Research Workspace

An institutional-grade stock research workstation integrating **FastAPI**, **PostgreSQL** via **SQLAlchemy**, signed **JWT token authentication**, and a responsive **React.js + Tailwind CSS** frontend.

---

## 🌟 Tech Stack Architecture

- **Frontend**: React.js (Vite), Tailwind CSS, Lucide Icons
- **Backend**: FastAPI (Python 3.15), Pydantic v2
- **Database**: PostgreSQL (psycopg3 & psycopg2-binary driver support with auto-fallback to SQLite for seamless offline testing)
- **Security**: JWT (HMAC-SHA256), Bcrypt password hashing, HTTPBearer token dependency
- **Data Integrations**: Support for Indian Stock Market APIs (NSE/BSE), Yahoo Finance quotes, and curated equity catalog

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

### Market Intelligence (`/api/v1/stocks`)
- `GET /stocks/search?query={q}`: Lookup stock symbols and company names
- `GET /stocks/quote/{ticker}?market={market}`: Real-time price and momentum feed

---

## 🚀 Quick Start Guide

### 1. Run the Integration Tests
Verify all 12 backend services, security guards, duplicate prevention, and token authentication:
```powershell
$env:PYTHONPATH = "$PWD\backend"
.\backend\venv\Scripts\python.exe .\backend\test_direct.py
```

### 2. Start the FastAPI Backend
```powershell
# Using the startup script:
.\start_backend.bat
# Or via powershell:
.\start_backend.ps1
```
Backend will be available at: **http://127.0.0.1:8000**
Interactive API Swagger Docs: **http://127.0.0.1:8000/docs**

### 3. Start the React Frontend
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

