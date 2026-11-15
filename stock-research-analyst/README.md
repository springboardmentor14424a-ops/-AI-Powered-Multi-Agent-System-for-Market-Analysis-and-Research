# Multi-Agent Stock Research Analyst — Module 1
## User Authentication and Research Workspace

**Stack:** React.js + Tailwind CSS · FastAPI (Python) · PostgreSQL · SQLAlchemy · Pydantic · JWT · bcrypt

## What's implemented (maps to the Module 1 guide)

| Guide section | Where it lives |
|---|---|
| 1. User registration (name, email, password, confirm) | `backend/app/routers/auth.py`, `frontend/src/pages/Register.jsx` |
| 2. User login with clear error messages | `auth.py` (`/login`), `pages/Login.jsx` |
| 3. JWT authentication (user id + expiry only, HTTP-only cookie, CSRF protection) | `security.py`, `deps.py` |
| 4. User-specific research history (statuses, open report) | `routers/research.py`, `components/ResearchHistory.jsx` |
| 5. Saved stocks / watchlist (search, add, list, remove, start research, no duplicates) | `routers/watchlist.py`, `routers/stocks.py`, `components/Watchlist.jsx` |
| 6. Preferences: market (NSE/BSE/NASDAQ/NYSE) and period (1M/3M/6M/1Y/5Y) | `routers/preferences.py`, `components/Preferences.jsx` |
| 7. PostgreSQL tables, keys, unique constraints, indexes | `backend/app/models.py`, `database/schema.sql` |
| 8. React ↔ FastAPI ↔ PostgreSQL request flow | `frontend/src/api.js` |

### Security points from the guide
- Passwords are hashed with **bcrypt**; only `password_hash` is stored.
- Login errors are generic ("Invalid email or password") so emails can't be enumerated.
- JWT contains only `sub` (user id), `iat`, `exp` and a CSRF value — no passwords or personal data.
- JWT is sent in an **HTTP-only** cookie; state-changing requests also need the `X-CSRF-Token` header
  (checked against the signed token).
- **`user_id` is never taken from the browser.** Every protected endpoint derives it from the verified JWT
  (`deps.get_current_user`), and all history/watchlist queries filter on it. Other users' records return 404.
- Duplicate watchlist entries are blocked by both an app check and a DB unique constraint `(user_id, ticker)`.

### Note on the research workflow
Module 1 only needs research tasks to be created, owned by a user and tracked through
`Pending → Processing → Completed/Failed`. `backend/app/workflow_stub.py` is a **placeholder** that
produces a dummy report after a few seconds. The real multi-agent analysis replaces it in later modules.

### Stock search (Yahoo Finance)
Stock search and ticker validation use **Yahoo Finance via the open-source `yfinance` library**
(`backend/app/yahoo_search.py`, wired in through `stock_service.py`). Results are limited to equities on NSE (`.NS`),
BSE (`.BO`), NASDAQ and NYSE, cached for 10 minutes, and each result shows its Yahoo symbol (e.g. `TCS.NS`).

If Yahoo is unreachable, rate-limits the request, or `yfinance` isn't installed, search automatically falls back
to a small built-in ticker list (`backend/app/stock_catalog.py`), so the app keeps working. The UI labels each
result "Yahoo Finance" or "built-in list". Set `YAHOO_SEARCH_ENABLED=false` in `.env` to force the built-in list.

## Run it locally

### 1. Database (PostgreSQL)
```bash
docker compose up -d        # or use your own Postgres and edit DATABASE_URL
```

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then set SECRET_KEY (command inside the file)
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs · health check: http://localhost:8000/api/health

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (Vite proxies `/api` to the backend, so cookies work without CORS issues).

### 4. Tests (backend)
```bash
cd backend
pytest -v
```
Tests use in-memory SQLite and cover registration, login, JWT/cookie/CSRF handling, per-user isolation of
history and watchlist, preferences and duplicate prevention.

## API summary (all under `/api`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | – | Create account |
| POST | `/auth/login` | – | Verify credentials, set cookies |
| POST | `/auth/logout` | – | Clear cookies |
| GET | `/auth/me` | ✓ | Current user |
| GET / PUT | `/preferences` | ✓ | Read / save market + period |
| GET | `/stocks/search?q=&market=` | ✓ | Search companies |
| GET / POST | `/watchlist` | ✓ | List / add saved stock |
| DELETE | `/watchlist/{id}` | ✓ | Remove saved stock |
| POST | `/research` | ✓ | Start research (uses saved prefs by default) |
| GET | `/research` | ✓ | Logged-in user's history |
| GET | `/research/{id}` | ✓ | One task + report |

## Manual test checklist (registration → dashboard)
1. Register a user (try a weak password and a duplicate email to see the errors).
2. Log in with a wrong password (clear error), then the right one → dashboard opens.
3. Preferences: choose NSE + 6 Months, save, refresh the page — values persist.
4. Watchlist: search "tcs", add it, try adding again (blocked), remove it.
5. Research: start research from search or from the watchlist → status goes Pending → Processing → Completed; open the report.
6. Register a second user in a private window — they see none of the first user's data.
7. Log out; `/dashboard` redirects to the login page.

## Submitting to Git
```bash
cd stock-research-analyst
git init
git add .
git status            # make sure .env and node_modules are NOT listed
git commit -m "Module 1: user authentication and research workspace"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```
