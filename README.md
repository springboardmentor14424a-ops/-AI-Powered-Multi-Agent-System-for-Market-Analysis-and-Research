# Multi-Agent Stock Research Analyst: Module 1 (Authentication)

React (Vite) frontend + FastAPI backend + PostgreSQL.
Landing page → Sign up → Sign in → protected Dashboard.

## Run it

**1. PostgreSQL** (Docker, or any local Postgres with a `stock_analyst` database)
```bash
docker compose up -d
```

**2. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then set JWT_SECRET (command is inside the file)
uvicorn app.main:app --reload --port 8000
```
The `users` table is created automatically on startup. API docs: http://localhost:8000/docs

**3. Frontend**
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```
Vite proxies `/api` to port 8000, so the browser sees one origin (cookies work, no CORS fuss).

**Tests:** `cd backend && python -m pytest` (87 tests; they use an in-memory SQLite DB and synthetic market data, so no internet is needed)

## Datasets and the analysis agents

"Run analysis" now runs four rule-based agents on real data and writes a combined report (no API key or paid service needed).

| Agent | Looks at | Data it uses |
|---|---|---|
| Technical | trend (50/200-day averages), MACD, RSI, momentum, 52-week position | **Yahoo Finance** prices via `yfinance` (live); **Kaggle NIFTY-50** CSVs as an offline NSE fallback |
| Sentiment | headline sentiment over the analysis window | **FNSPID** (US news), **Indian_Financial_News** (NSE/BSE), live Yahoo headlines; scored by a model trained on **Financial PhraseBank + FiQA + Twitter financial news** |
| Fundamentals | revenue growth, margins, ROE, leverage, P/E | **SEC EDGAR** company facts (US, official filings), **Yahoo Finance** fundamentals (all markets) |
| Risk | volatility, drawdown, 1-day VaR, beta, market fear gauge | prices + market index (`^GSPC` / `^NSEI` / `^BSESN`), **FRED VIX** (US), **India VIX** |

Each rule adds or subtracts a fixed amount, so every number in the report can be traced to a sentence in it. Scores combine with weights Technical 30%, Fundamentals 30%, Sentiment 25%, Risk 15%.

**What works with no downloads at all** (just an internet connection): live prices, fundamentals, market index, VIX and the latest Yahoo headlines. The downloads below add history for sentiment, an offline NSE fallback, and the trained sentiment model.

```bash
cd backend
pip install -r requirements-data.txt          # download helpers (Hugging Face, Kaggle)
python -m scripts.download_data check         # what you have so far
python -m scripts.download_data sentiment     # PhraseBank + FiQA + Twitter news  (small)
python -m scripts.download_data prices        # Kaggle NIFTY-50                   (small; may ask for a free Kaggle login)
python -m scripts.download_data news          # Indian_Financial_News + FNSPID    (FNSPID is streamed: slow, but nothing big is saved)
python -m scripts.train_sentiment             # trains in seconds, saves data/models/sentiment.joblib
```
Restart the backend after training. Everything lands in `backend/data/` (ignored by git). If an automatic download fails, the script prints the dataset page and the folder to put the file in; any CSV placed there is picked up. Until you train the model, the Sentiment agent uses a small keyword list and says so in the report.

**Optional:** to use official SEC filings for US fundamentals, set `SEC_USER_AGENT=Your Name your@email.com` in `backend/.env` (the SEC requires clients to identify themselves). Without it the app uses Yahoo Finance fundamentals.

**Behaviour to know about**
- If one agent can't get its data, the report marks it "Unavailable" with the reason and still completes. If no price data can be found at all, the task fails with a clear message.
- Old prices (e.g. the 2021 Kaggle fallback) get a *STALE DATA* banner and confidence is forced to Low.
- The offline datasets are historical, so the Sentiment agent states the date range of the headlines it used.
- Licences differ: Financial PhraseBank is non-commercial (fine for coursework), FNSPID is CC BY 4.0, Kaggle datasets vary by page, and Yahoo Finance data is for personal use. Check before any commercial use.
- Not used (too large or not an open API): EDGAR-CORPUS 10-K text, FinQA / FinanceBench (these are for evaluating LLM answers), and Screener.in (no public API).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Validate, reject duplicate email, bcrypt-hash, insert user |
| POST | `/api/auth/login` | Verify password, set JWT cookie + CSRF cookie |
| GET  | `/api/auth/me` | Restore session after a page reload |
| POST | `/api/auth/logout` | Clear cookies |
| GET  | `/api/dashboard` | Example protected route |
| POST | `/api/research` | Create a research task for the logged-in user and start the workflow |
| GET  | `/api/research` | List **only the logged-in user's** tasks (newest first) |
| GET  | `/api/research/{id}` | One task with its report (404 if it isn't yours) |
| GET  | `/api/stocks/search?q=&market=` | Search the validated ticker list by company name or ticker |
| GET  | `/api/watchlist` | The logged-in user's saved stocks |
| POST | `/api/watchlist` | Save a stock (`{ticker, market}`); 409 if already saved, 404 if unsupported |
| DELETE | `/api/watchlist/{id}` | Remove a saved stock (404 if it isn't yours) |
| GET / PUT | `/api/preferences` | Read / save preferred market and default analysis period |

## `users` table

| Column | Type | Notes |
|---|---|---|
| id | serial PK | |
| full_name | varchar(100) | |
| email | varchar(254) | **UNIQUE**, stored lowercase |
| password_hash | varchar(128) | bcrypt hash only, never the password |
| created_at | timestamptz | default `now()` |

## `research_tasks` table

| Column | Type | Notes |
|---|---|---|
| id | serial PK | |
| user_id | int FK → users.id | indexed, `ON DELETE CASCADE`; set from the JWT, never from the request |
| company_name, ticker, market, analysis_period | varchar | ticker stored uppercase |
| status | varchar | `pending` → `processing` → `completed` or `failed` |
| report | text | filled when completed |
| error | text | clear failure message when failed |
| created_at, completed_at | timestamptz | |

## Research history (guide section 4)

- Starting research creates a task tied to the authenticated user, then `workflow.py` runs in a background task and updates the status.
- **The agents are placeholders.** `generate_report()` in `backend/app/workflow.py` returns a stub report so the full pipeline works now. Replace that one function with the real multi-agent workflow later.
- Failures are caught, logged on the server, and saved as `failed` with a safe user-facing message. Tasks left `pending`/`processing` by a server restart are marked `failed` on the next startup.
- The dashboard shows company, ticker, market, period, date and status, refreshes automatically while tasks run, and lets you open completed reports at `/research/:id`.
- **Security:** the request model has no `user_id` field; every query filters on the user from the verified JWT. Another user's task returns 404, as if it didn't exist.

## Watchlist and preferences (guide sections 5 and 6)

Tables (primary keys are named as in the guide: `user_id`, `task_id`, `saved_stock_id`):

| Table | Key columns |
|---|---|
| `saved_stocks` | `saved_stock_id` PK, `user_id` FK, `ticker`, `company_name`, `market`, `created_at`; **UNIQUE (user_id, market, ticker)** |
| `user_preferences` | `user_id` PK/FK (one row per user), `preferred_market`, `default_analysis_period`, `updated_at` |

- **Markets:** NSE, BSE, NASDAQ, NYSE. Ticker format is validated per market: NSE `RELIANCE`, BSE 6-digit scrip code `500325`, US `AAPL`. A pasted `.NS` / `.BO` suffix is accepted and removed. `provider_symbol()` in `app/stocks.py` converts to `RELIANCE.NS` / `500325.BO` for data providers.
- **Stock search** uses a curated list of about 70 well-known listings in `backend/app/stocks.py` (not the full exchanges). To use a live provider, replace `search_stocks()` and `find_stock()` there.
- **Watchlist:** the server looks the company name up itself (it never trusts one from the browser), blocks duplicates with the database constraint, and only ever touches the logged-in user's rows. "Research" on a saved stock starts a task using the user's default period.
- **Preferences** load when the dashboard opens and pre-fill the search market and the new-research form. The chosen market and period are stored on the task and used by the workflow (the placeholder report shows e.g. `~365 days of daily prices for RELIANCE.NS`).

## Upgrading an existing local database

The primary-key columns were renamed to match the guide, and `create_all` does not alter existing tables. With no data you need to keep, reset the tables once: in psql, connect to `stock_analyst` and run
`DROP TABLE IF EXISTS user_preferences, saved_stocks, research_tasks, users CASCADE;`
then restart the backend and it recreates them.

## How the requirements map to the code

- **Validation:** `backend/app/schemas.py` (email format, password rules, confirm match); the same rules run client-side in `Register.jsx` for instant feedback.
- **Duplicate email:** checked in `routers/auth.py`, backed by the UNIQUE index so concurrent sign-ups can't slip through.
- **Hashing:** bcrypt in `security.py`. Cost factor 12.
- **Login errors:** one generic "Incorrect email or password." for both unknown email and wrong password, plus a dummy hash check so timing doesn't reveal which emails exist.
- **JWT:** payload is only `sub` (user id), `iat`, `exp`; signed HS256; 60-minute expiry (`security.py`).
- **Token storage:** HTTP-only, `Secure`, `SameSite=Lax` cookie, so JavaScript can't read the token.
- **CSRF:** double-submit token. Login also sets a readable `csrf_token` cookie; state-changing cookie-authenticated requests must echo it in `X-CSRF-Token` (`deps.py`, `frontend/src/api.js`).
- **Bearer support:** `Authorization: Bearer <jwt>` is also accepted (no CSRF needed, since browsers don't attach it automatically).
- **Missing/invalid/expired token:** 401 → the frontend clears state and redirects to `/login` with "session expired".

## Before deploying
- Serve over **HTTPS** and keep `COOKIE_SECURE=true` (`false` is for local http only).
- Set a long random `JWT_SECRET` and keep it out of git.
- Add login rate-limiting (e.g. `slowapi`) and Alembic migrations.
- If the frontend and API are on different domains, set `CORS_ORIGINS` and use `COOKIE_SAMESITE=none` (requires HTTPS).
