# Multi-Agent Stock Research Analyst

The current implementation covers user authentication and preferences, PostgreSQL-backed watchlists and research history, Yahoo Finance stock search and historical market data, and a rule-based Fundamental Analysis Agent. All stock profiles, financial statements, peer information, and price records are retrieved with the Python `yfinance` module.

## Run the application

### Start PostgreSQL

```powershell
docker compose up -d postgres
```

### Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The default connection is `postgresql+psycopg://postgres:postgres@localhost:5433/stock_research`. Port `5433` avoids conflicting with a locally installed PostgreSQL server already using port `5432`. Change `DATABASE_URL` in `.env` to use another PostgreSQL server.

### Run the frontend

```powershell
cd C:\InfosysSpringboard\frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`.

### Enable Google sign-in (optional)

1. Create a **Web application** OAuth client in Google Cloud Console and configure the OAuth consent screen.
2. Add the exact local frontend origin you use (for example `http://localhost:5173` or `http://127.0.0.1:5173`) to the client's authorized JavaScript origins.
3. Set `GOOGLE_CLIENT_ID` in `backend/.env` to the client ID, then restart FastAPI.

The client ID is public and is used by both Google Identity Services in the browser and the backend's ID-token audience verification. Google sign-in remains unavailable until it is configured. Only Google-verified email addresses are accepted.

## Available features

- User registration and login with JWT authentication and an HTTP-only cookie.
- Optional Google sign-in with backend-verified ID tokens.
- Per-user market and analysis-period preferences (United States, NSE, or BSE).
- Per-user saved stocks grouped into named watchlists.
- Per-user history of completed and failed fundamental analysis tasks and their reports.
- Stock search by company name or ticker, powered by Yahoo Finance through `yfinance`.
- Historical OHLCV retrieval with duplicate-date, missing-value, and inconsistent-price validation.
- Fundamental analysis of reported annual revenue, earnings, debt, cash, equity, valuation and profitability ratios, plus same-industry peer comparisons where data is available.
- Source links, retrieval timestamps, data gaps, and calculation limitations in analysis results.

The backend creates the PostgreSQL tables on startup. The database uses a Docker named volume, so stopping the containers does not remove saved records.

## Dashboard template

The React dashboard layout is adapted from [TailAdmin's free React Tailwind dashboard](https://github.com/TailAdmin/free-react-tailwind-admin-dashboard), with its sidebar, workspace cards, and navigation tailored to this application. The original template is MIT-licensed; see [frontend/TAILADMIN_LICENSE.txt](./frontend/TAILADMIN_LICENSE.txt).

## API endpoints

- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/google`, `GET /api/auth/google/config`, `GET /api/auth/me`, `POST /api/auth/logout`
- `GET /api/preferences`, `PUT /api/preferences` - read/update the user's market and period.
- `GET /api/stocks/search?q=Apple&market=US` - authenticated company/ticker search. Supported markets: `US`, `NSE`, `BSE`.
- `GET /api/stocks/{ticker}/market-data?period=1y&market=US` - authenticated OHLCV history.
- `GET /api/stocks/saved`, `POST /api/stocks/saved`, `DELETE /api/stocks/saved/{saved_stock_id}` - manage watchlist entries.
- `POST /api/research/fundamental` - authenticated fundamental analysis; JSON body: `{"ticker":"AAPL","period":"1y","market":"US"}`.
- `GET /api/research/history`, `GET /api/research/history/{task_id}` - list/open the user's stored research reports.
- `GET /docs` - interactive API documentation.

Yahoo Finance data availability varies by ticker and market. Missing values are reported rather than inferred. Fundamental metrics describe reported historical/company data and are informational, not investment advice. Technical analysis, news, risk assessment, supervisor orchestration, and consolidated reports are not implemented yet.

## Tests

From `backend`, run:

```powershell
pytest
```
