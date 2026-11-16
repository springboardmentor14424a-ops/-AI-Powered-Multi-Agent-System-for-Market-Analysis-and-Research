# StockMind AI — Multi-Agent Stock Research Analyst

An AI-powered stock research and market analysis platform.

## Architecture

- **Frontend**: React 19, Vite, Tailwind CSS v4, React Router DOM, Axios, Lucide React, Recharts, Framer Motion
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, PyJWT, Argon2 (`pwdlib`)
- **Market Data**: Yahoo Finance (`yfinance`), Pandas

## Features (Milestone 1)

- 🔒 **Full Authentication Flow**: Register, Login with JWT session and Argon2 password hashing
- 🛡️ **PostgreSQL Integration**: Managed via Alembic migrations
- 📈 **Real-Time Stock Search & History**: Interactive price charts (1M, 3M, 6M, 1Y, 5Y) via Recharts
- ⚡ **Fintech Landing Page & Dashboard**: Glassmorphic dark UI with responsive navigation

## Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PostgreSQL credentials

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:5173` and communicate with the backend at `http://localhost:8000`.

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

