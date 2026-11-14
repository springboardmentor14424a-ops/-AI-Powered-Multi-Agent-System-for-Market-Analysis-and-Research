# AI-Powered Multi-Agent System for Market Analysis and Research

## Project Overview

This project aims to develop an AI-powered system for stock market analysis and research. It helps users explore stock market information through an interactive web application.

## Features

- User Registration and Login
- Google Sign-In
- JWT-based Authentication
- Stock Market Data using Yahoo Finance
- Historical Stock Price Charts
- Personal Watchlist Management
- Add and Remove Stocks from Watchlist
- User-specific Watchlists

## Technologies Used

**Frontend:**
- React.js
- Vite
- Axios
- Recharts
- CSS

**Backend:**
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- Yahoo Finance (`yfinance`)

## Project Structure

```text
project/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    ├── package.json
    └── package-lock.json
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Backend Setup

```bash
cd backend
python -m venv aiintern
```

Activate the virtual environment:

**Windows:**
```bash
aiintern\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## Configuration

Create a `.env` file inside the backend directory and configure the required database credentials, authentication settings, and Google Sign-In credentials.

Do not commit your `.env` file or expose secret keys publicly.

## Project Status

**Module 1 – Completed**

- Authentication
- Stock Data Integration
- Historical Stock Charts
- Watchlist Management

Further modules and AI-powered multi-agent features will be developed as the project progresses.

## Internship

**Infosys Springboard Internship Project**