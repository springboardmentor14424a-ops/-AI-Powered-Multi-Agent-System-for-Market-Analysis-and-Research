# Multi-Agent Stock Research Analyst - Module 1

User authentication and research workspace.

- `backend/`  FastAPI + PostgreSQL (registration, login, JWT, watchlist, preferences)
- `frontend/` React (landing page, sign up, sign in, dashboard)

## Run the backend
    cd backend
    py -3.13 -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env      (then edit .env)
    uvicorn main:app --reload

## Run the frontend
    cd frontend
    npm install
    npm run dev
