# AI-Powered Multi-Agent System for Market Analysis and Research

An AI-powered stock research platform designed to help users explore stocks, retrieve historical market data, and access structured investment research through a multi-agent architecture.

## Technology Stack

### Frontend
- React
- Vite
- JavaScript
- CSS
- Google OAuth

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- Google ID Token Verification
- yfinance for market data retrieval

## Project Structure

```text
AI-Powered-Multi-Agent-System/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── setup_database.py
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following before running the application:

- Python 3.10 or later
- Node.js and npm
- PostgreSQL
- Git

## Setup Instructions

### 1. Clone the Repository

This project is configured for individual evaluation. The following command clones the `Akshita-Kannappan` branch directly.

```bash
git clone -b Akshita-Kannappan https://github.com/springboardmentor14424a-ops/-AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research.git
cd -AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research
```

Replace `<repository-url>` with the full GitHub repository URL.

### 2. Backend Setup

Create and activate a virtual environment from the project root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

### 3. Configure Backend Environment

Copy the example environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Configure the following variables in `backend/.env`:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Secret key used for JWT authentication |
| `DATABASE_URL` | PostgreSQL database connection URL |
| `CORS_ORIGINS` | Allowed frontend origins |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```text
stock_analyst
```

Ensure that `DATABASE_URL` in `backend/.env` contains the correct PostgreSQL username, password, host, and database name.

Initialize the database tables:

```powershell
cd backend
python setup_database.py
```

### 5. Start the Backend

From the `backend` directory, with the virtual environment activated:

```powershell
uvicorn main:app --reload
```

Backend API:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 6. Frontend Setup

Open a second terminal and navigate to the frontend directory:

```powershell
cd frontend
npm install
```

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configure `VITE_GOOGLE_CLIENT_ID` in `frontend/.env` with the Google OAuth client ID.

Start the frontend:

```powershell
npm run dev
```

Frontend:

`http://localhost:5173`

## Current Features

- User registration and login
- Google OAuth authentication
- JWT-based authentication
- PostgreSQL-backed user and preference storage
- Stock search
- Historical market data retrieval
- Support for NSE, BSE, and US market symbols
- User preferences for market data periods
- Watchlist functionality

## Supported Historical Data Periods

- 1 month
- 3 months
- 6 months
- 1 year
- 2 years
- 5 years
- 10 years
- Year to date
- Maximum available history

## Security Notes

- Never commit `.env` files or expose credentials.
- Keep `SECRET_KEY` private and use a secure value.
- Keep Google OAuth credentials private.
- Use `.env.example` files as configuration templates only.

