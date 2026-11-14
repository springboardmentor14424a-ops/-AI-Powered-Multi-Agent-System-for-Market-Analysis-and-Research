# AI-Powered Multi-Agent System for Market Analysis and Research

## 1. Project Overview

The AI-Powered Multi-Agent System for Market Analysis and Research is a stock research platform designed to help users explore stock market information, manage research activities, and organise stock-related insights.

The platform provides user authentication, a personalised research workspace, stock search, watchlists, research history, and user preferences.

The project is being developed using React.js, FastAPI, Python, and PostgreSQL.

## 2. Technologies Used

### Frontend
- React.js
- Vite
- JavaScript
- CSS
- Axios
- React Router

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- bcrypt
- Uvicorn

### Database
- PostgreSQL

### Market Data
- Yahoo Finance (yfinance)
- TejHQ API for BSE market data

### Testing and Development
- Postman
- Visual Studio Code
- Git and GitHub

## 3. Project Structure

```text
AI-Powered-Multi-Agent-System-for-Market-Analysis-and-Research/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── test_db.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
│
├── postman/
├── .gitignore
└── README.md

