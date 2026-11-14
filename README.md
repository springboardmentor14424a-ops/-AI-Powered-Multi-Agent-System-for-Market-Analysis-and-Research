# Multi-Agent Stock Research Analyst

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.1.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4.17-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, multi-tenant stock research and financial analysis platform. This application provides automated equity research dossiers, real-time status tracking, personalized stock watchlists, dynamic exchange-filtered autocomplete, and enterprise-grade session authentication across **NASDAQ**, **NYSE**, **NSE** (India), and **BSE** (India).

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
  - [Primary Purpose](#primary-purpose)
  - [Core Functionalities](#core-functionalities)
  - [Application Architecture](#application-architecture)
- [2. Complete Technology Stack](#2-complete-technology-stack)
- [3. Project Folder Structure](#3-project-folder-structure)
- [4. Prerequisites and Software Installation](#4-prerequisites-and-software-installation)
  - [Prerequisites Checklist](#prerequisites-checklist)
  - [Windows Installation Instructions](#windows-installation-instructions)
- [5. PostgreSQL Database Setup](#5-postgresql-database-setup)
  - [Step 1: Install PostgreSQL](#step-1-install-postgresql)
  - [Step 2: Start the PostgreSQL Service](#step-2-start-the-postgresql-service)
  - [Step 3: Connect via psql CLI](#step-3-connect-via-psql-cli)
  - [Step 4: Create Application Database](#step-4-create-application-database)
  - [Step 5: Database Schema (SQL DDL)](#step-5-database-schema-sql-ddl)
  - [Step 6: Database Troubleshooting](#step-6-database-troubleshooting)
- [6. Environment Variables and Configuration](#6-environment-variables-and-configuration)
  - [Backend Environment Variables (`backend/.env`)](#backend-environment-variables-backendenv)
  - [Frontend Environment Variables (`frontend/.env`)](#frontend-environment-variables-frontendenv)
  - [Obtaining a Google OAuth Client ID](#obtaining-a-google-oauth-client-id)
- [7. Backend Setup and Execution](#7-backend-setup-and-execution)
- [8. Frontend Setup and Execution](#8-frontend-setup-and-execution)
- [9. Complete API Documentation](#9-complete-api-documentation)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Preferences Endpoints](#user-preferences-endpoints)
  - [Watchlist & Company Autocomplete Endpoints](#watchlist--company-autocomplete-endpoints)
  - [Stock Research Tasks & Reports Endpoints](#stock-research-tasks--reports-endpoints)
  - [System & Health Endpoints](#system--health-endpoints)
- [10. Google Authentication Integration](#10-google-authentication-integration)
- [11. Stock Research Workflow & Status Lifecycle](#11-stock-research-workflow--status-lifecycle)
- [12. Research History Management](#12-research-history-management)
- [13. Personal Stock Watchlist](#13-personal-stock-watchlist)
- [14. Database Schema and Entity-Relationship Diagram](#14-database-schema-and-entity-relationship-diagram)
- [15. Zero-to-Running: Developer Execution Guide](#15-zero-to-running-developer-execution-guide)
  - [Quick-Start (Prerequisites Already Installed)](#quick-start-prerequisites-already-installed)
  - [Detailed Step-by-Step Guide](#detailed-step-by-step-guide)
  - [One-Click Windows Launcher](#one-click-windows-launcher)
- [16. Automated Testing and Verification](#16-automated-testing-and-verification)
- [17. Security Architecture](#17-security-architecture)
- [18. Troubleshooting Matrix](#18-troubleshooting-matrix)
- [19. Contributing and Git Workflow](#19-contributing-and-git-workflow)

---

## 1. Project Overview

### Primary Purpose
Conducting rigorous fundamental and technical equity research typically requires analysts to manually aggregate data from disjoint sources: historical price charts, valuation multiples, corporate earnings, technical moving averages, and analyst consensus ratings.

The **Multi-Agent Stock Research Analyst** solves this problem by providing a centralized workspace where authenticated users can:
1. Select their primary exchange market and historical analysis window.
2. Search and discover listed companies using strict, exchange-filtered prefix autocomplete.
3. Launch automated research pipelines that pull dynamic market data and compile structured equity research dossiers.
4. Track research tasks through an asynchronous lifecycle (**Pending** $\rightarrow$ **Processing** $\rightarrow$ **Completed** / **Failed**).
5. Maintain a personal stock watchlist with live pricing and one-click **"Research Now"** execution.
6. Inspect, manage, and delete individual research history entries with strict multi-tenant data isolation.

### Core Functionalities
- **User Authentication & Session Security**: Secure registration, bcrypt password hashing, signed JWT tokens, HTTP-only SameSite session cookies, 15-minute inactivity timeouts, server-side session revocation on logout, and Google Sign-In (OAuth 2.0 / OpenID Connect).
- **Workspace Preferences**: User-configurable default exchange market (`NSE`, `BSE`, `NASDAQ`, `NYSE`) and default historical analysis window (`1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`), persisted to PostgreSQL.
- **Dynamic Company Autocomplete**: Strict prefix-based search (`company.name.toLowerCase().startsWith(query)`) restricted to the user's selected exchange market. Prevents cross-exchange leakage and eliminates substring mismatch bugs.
- **Asynchronous Equity Research**: Background task execution via FastAPI `BackgroundTasks`. Generates dossiers containing:
  - **Asset Profile**: Company name, ticker, sector, industry, market capitalization.
  - **Historical Performance**: Trading days, start/close prices, period return %, period high/low, average volume.
  - **Fundamental Indicators**: Trailing P/E, Forward P/E, Trailing EPS, Wall Street consensus target price, and analyst consensus rating (`BUY`, `HOLD`, `SELL`).
  - **Technical Moving Averages**: 50-day moving average, 200-day moving average, and 52-week price range.
  - **Recent OHLCV Records**: Tabular breakdown of the most recent daily trading sessions.
- **Stock Watchlist**: Add stocks directly from search results or from research report dossiers. Displays real-time prices, daily change %, currency, and a one-click **"▶ Research Now"** trigger with duplicate prevention.
- **Research History & Deletion**: Tabular view of all historical tasks with status badges and an individual trash action backed by a modal confirmation dialog.

### Application Architecture

```mermaid
graph TD
    User([Browser / Client])
    
    subgraph Frontend ["Frontend (React 18 + Vite :5173)"]
        UI[Tailwind CSS Components]
        AuthCtx[AuthContext & Session Manager]
        AxiosClient[Axios API Client (/api)]
    end

    subgraph Backend ["Backend (FastAPI :8000)"]
        RouterAuth["/api/auth (Login, Register, Google, Logout)"]
        RouterPref["/api/preferences (User Settings)"]
        RouterWatch["/api/watchlist (Search, Watchlist CRUD)"]
        RouterTasks["/api/tasks (Async Research Pipeline)"]
        Security[Bcrypt + PyJWT + Session Engine]
        BgWorker[FastAPI BackgroundTasks Worker]
    end

    subgraph External ["External Services"]
        YF[Yahoo Finance API / yfinance]
        GoogleOAuth[Google Identity Services / OAuth 2.0]
    end

    subgraph Database ["Persistence Layer"]
        PG[(PostgreSQL 16 :5432)]
    end

    User -->|Interacts| UI
    UI --> AuthCtx
    AuthCtx --> AxiosClient
    AxiosClient -->|Reverse Proxy /api| RouterAuth
    AxiosClient -->|Reverse Proxy /api| RouterPref
    AxiosClient -->|Reverse Proxy /api| RouterWatch
    AxiosClient -->|Reverse Proxy /api| RouterTasks

    RouterAuth --> Security
    Security -->|Verify / Store Session| PG
    RouterPref -->|Read / Write Preferences| PG
    RouterWatch -->|Manage Saved Stocks| PG
    RouterWatch -->|Live Quotes| YF
    RouterTasks -->|Insert Pending Task| PG
    RouterTasks -->|Dispatch Background Job| BgWorker

    BgWorker -->|Fetch Historical OHLCV & Fundamentals| YF
    BgWorker -->|Save Dossier & Mark Completed| PG

    UI -.->|Sign In with Google| GoogleOAuth
    GoogleOAuth -.->|ID Token Credential| RouterAuth
```

---

## 2. Complete Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React.js | `^18.3.1` | Declarative component UI library for SPA rendering. |
| **Build Tool & Bundler** | Vite | `^6.1.0` | Ultra-fast development server with Hot Module Replacement (HMR) and production bundler. |
| **Styling & Design** | Tailwind CSS | `^3.4.17` | Utility-first CSS framework for modern dark-themed financial UI. |
| **Icons** | Lucide React | `^0.475.0` | Vector icon set for clean, accessible UI actions and status badges. |
| **HTTP Client** | Axios | `^1.7.9` | Promise-based HTTP client with `withCredentials: true` and 401 response interceptors. |
| **Routing** | React Router DOM | `^7.1.5` | Client-side routing with `ProtectedRoute` navigation guards. |
| **Backend Framework** | FastAPI | `>=0.115.0` | High-performance asynchronous Python web framework with automatic OpenAPI docs. |
| **ASGI Web Server** | Uvicorn | `>=0.30.0` | Production-grade lightning-fast ASGI server. |
| **Programming Language** | Python | `3.10 - 3.13` | Modern Python runtime for backend and financial data processing. |
| **Database ORM** | SQLAlchemy | `>=2.0.35` | Object-Relational Mapping library with declarative models and relation cascading. |
| **Database Driver** | Psycopg2-binary | `>=2.9.9` | PostgreSQL database adapter for Python. |
| **Primary Database** | PostgreSQL | `14+ / 16` | Relational database for users, sessions, preferences, watchlists, tasks, and reports. |
| **Data Validation** | Pydantic v2 | `>=2.9.0` | Strict data parsing, type validation, and serialization with `pydantic-settings`. |
| **Password Hashing** | Bcrypt | `>=4.0.1` | Secure password hashing algorithm using 12 salt rounds. |
| **Token Authentication** | PyJWT | `>=2.9.0` | Cryptographic JSON Web Token encoding and decoding (HS256 algorithm). |
| **Market Data Provider** | Yahoo Finance (`yfinance`)| `>=1.8.0` | Real-time and historical financial datasets, valuation multiples, moving averages, and OHLCV bars. |
| **Third-Party Auth** | Google Identity Services | GIS / OAuth 2.0 | Cryptographic Google Single Sign-On using OpenID Connect and Google ID tokens. |
| **Automated Testing** | Pytest & HTTPX | `>=8.3.0` | Integration and unit testing framework for API routes and business logic. |
| **Containerization** | Docker & Docker Compose | Compose v3.8 | Multi-container development orchestration for PostgreSQL and FastAPI. |

---

## 3. Project Folder Structure

```text
infosys_spring_board/
├── docker-compose.yml              # Multi-container orchestration (PostgreSQL + FastAPI)
├── README.md                       # Comprehensive project documentation (this file)
├── start_app.bat                   # Windows batch launcher (starts backend, frontend, browser)
├── view_db.py                      # Database inspection CLI utility (displays tables/rows)
│
├── backend/                        # FastAPI Application Root
│   ├── Dockerfile                  # Container definition for Python 3.13 backend
│   ├── requirements.txt            # Python dependencies specification
│   ├── run.py                      # Direct server entry point (python run.py)
│   ├── .env                        # Local backend environment configuration (ignored in Git)
│   ├── .env.example                # Example backend environment variables template
│   │
│   ├── app/                        # Application Source Code
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic BaseSettings, boot timestamp, CORS origins
│   │   ├── database.py             # SQLAlchemy engine, SessionLocal, get_db generator
│   │   ├── dependencies.py         # Auth dependency (cookie/bearer resolution, inactivity check)
│   │   ├── main.py                 # FastAPI application instantiation, CORS, router mounting
│   │   ├── models.py               # SQLAlchemy ORM models (User, SavedStock, ResearchTask, etc.)
│   │   ├── schemas.py              # Pydantic request/response validation schemas
│   │   ├── security.py             # Password hashing (bcrypt 12 rounds), JWT encoding/decoding
│   │   │
│   │   ├── routers/                # API Route Controllers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # User registration, login, Google Sign-In, logout, /me
│   │   │   ├── preferences.py      # Market & analysis period user settings (GET, PUT)
│   │   │   ├── tasks.py            # Research task creation, async worker, report query, delete
│   │   │   └── watchlist.py        # Company search, exchange autocomplete, watchlist CRUD
│   │   │
│   │   └── services/               # External Integration & Domain Services
│   │       ├── __init__.py
│   │       └── market_data.py      # yfinance integration, ticker normalization, prefix filtering
│   │
│   └── tests/                      # Automated Test Suite
│       ├── conftest.py             # Pytest fixtures and Starlette TestClient setup
│       ├── test_auth_and_workspace.py         # Registration, login, preferences, isolation
│       ├── test_company_autocomplete.py       # Strict prefix matching, exchange isolation
│       ├── test_history_and_watchlist_features.py # Individual delete, status, duplicate checks
│       ├── test_session_management.py         # Inactivity timeout, cookie security, logout
│       └── test_tasks_4_5_6.py                # End-to-end tasks 4, 5, 6 verification script
│
└── frontend/                       # React.js SPA Root (Vite)
    ├── index.html                  # HTML entry point, Google Identity Services client script
    ├── package.json                # Node dependencies and scripts
    ├── postcss.config.js           # PostCSS configuration for Tailwind CSS
    ├── tailwind.config.js          # Tailwind styling configuration
    ├── vite.config.js              # Vite server configuration, port 5173, /api proxy to 8000
    ├── .env                        # Local frontend environment variables (ignored in Git)
    ├── .env.example                # Example frontend environment variables template
    │
    └── src/
        ├── App.jsx                 # Top-level router (Login, Register, Dashboard, ProtectedRoute)
        ├── index.css               # Tailwind CSS directives and custom scrollbar styling
        ├── main.jsx                # React DOM root render
        │
        ├── api/
        │   └── client.js           # Central Axios instance, withCredentials, 401 redirector
        │
        ├── components/             # Reusable UI Components
        │   ├── GoogleButton.jsx    # Google Identity Services button with OAuth guide fallback
        │   ├── GoogleSignInText.jsx# Google button text styling helper
        │   ├── Navbar.jsx          # Top navigation bar with user profile and logout button
        │   └── ProtectedRoute.jsx  # Route guard redirecting unauthenticated users to /login
        │
        ├── context/
        │   └── AuthContext.jsx     # User auth state, 15-min inactivity timer, login/logout handlers
        │
        └── pages/                  # Main View Pages
            ├── DashboardPage.jsx   # Tabbed research workspace, history, watchlist, report modal
            ├── LoginPage.jsx       # User login page with form and Google button
            └── RegisterPage.jsx    # User registration page with password confirmation
```

---

## 4. Prerequisites and Software Installation

### Prerequisites Checklist

| Software | Minimum Version | Recommended Version | Official Download Link | Verification Command |
| :--- | :--- | :--- | :--- | :--- |
| **Node.js** | `v18.0.0` | `v20.x LTS` | [nodejs.org](https://nodejs.org/) | `node -v` |
| **npm** | `9.0.0` | `10.x` | Bundled with Node.js | `npm -v` |
| **Python** | `3.10` | `3.11 / 3.12 / 3.13` | [python.org](https://www.python.org/downloads/) | `python --version` |
| **pip** | `23.0` | Latest | Bundled with Python | `pip --version` |
| **PostgreSQL** | `14.0` | `16.x` | [postgresql.org](https://www.postgresql.org/download/) | `psql --version` |
| **Git** | `2.30` | Latest | [git-scm.com](https://git-scm.com/) | `git --version` |
| **VS Code** | Latest | Latest | [code.visualstudio.com](https://code.visualstudio.com/) | `code -v` |

### Windows Installation Instructions

#### 1. Node.js & npm
1. Download the **Windows Installer (.msi) 64-bit** from [nodejs.org](https://nodejs.org/).
2. Run the installer and check the box to automatically install the necessary tools.
3. Open PowerShell and verify:
   ```powershell
   node -v
   npm -v
   ```

#### 2. Python & pip
1. Download the **Windows installer (64-bit)** for Python 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/windows/).
2. **CRITICAL STEP**: On the first installer screen, check **"Add python.exe to PATH"** before clicking **Install Now**.
3. Open a new PowerShell terminal and verify:
   ```powershell
   python --version
   pip --version
   ```

#### 3. PostgreSQL Database
1. Download the PostgreSQL 16 Windows interactive installer from [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. Run the installer. Leave components checked: **PostgreSQL Server**, **pgAdmin 4**, **Command Line Tools**.
3. Choose an installation directory (default: `C:\Program Files\PostgreSQL\16`).
4. **Set a superuser password**: Enter a secure password for the `postgres` user (e.g., `postgres` or your custom password) and **memorize it**.
5. Leave the port as default: `5432`.
6. Complete installation and uncheck Stack Builder at the end.
7. **Add PostgreSQL `bin` directory to Windows PATH**:
   - Open Windows Search $\rightarrow$ Type **"Environment Variables"** $\rightarrow$ Click **"Edit the system environment variables"**.
   - Under System Variables, select **Path** $\rightarrow$ Click **Edit**.
   - Click **New** $\rightarrow$ Paste: `C:\Program Files\PostgreSQL\16\bin` (adjust version number if necessary).
   - Click **OK** on all dialogs.
8. Open a new PowerShell terminal and verify:
   ```powershell
   psql --version
   ```

---

## 5. PostgreSQL Database Setup

### Step 1: Install PostgreSQL
Ensure PostgreSQL is installed following the instructions in [Section 4](#windows-installation-instructions).

### Step 2: Start the PostgreSQL Service
On Windows, PostgreSQL runs as a background service (`postgresql-x64-16`). Check its status or start it manually if needed:
```powershell
# Check service status
Get-Service -Name postgresql*

# Start service if stopped
Start-Service -Name postgresql*
```

### Step 3: Connect via psql CLI
Open PowerShell and connect to the local PostgreSQL server as the default superuser `postgres`:
```powershell
psql -U postgres -h localhost -p 5432
```
*When prompted for the password, type the password you entered during PostgreSQL installation (keystrokes will be hidden) and press Enter.*

### Step 4: Create Application Database
Once connected to the `postgres=#` prompt, execute:
```sql
-- Create the dedicated application database
CREATE DATABASE stock_analyst;

-- Confirm database creation
\l

-- Connect to the newly created database
\c stock_analyst;
```

### Step 5: Database Schema (SQL DDL)
> **Note**: When the backend starts, SQLAlchemy automatically creates all database tables via `Base.metadata.create_all(bind=engine)` in `app/main.py`. You do **not** need to manually execute SQL scripts. However, for database administrators or manual inspection, here is the exact DDL schema matching the ORM models:

```sql
-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_user_id ON users(user_id);

-- 2. User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preferred_market VARCHAR(20) NOT NULL DEFAULT 'NASDAQ',
    default_analysis_period VARCHAR(20) NOT NULL DEFAULT '1 Year',
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 3. User Sessions Table (Stateful Enterprise Session Security)
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);

-- 4. Saved Stocks (Watchlist) Table
CREATE TABLE IF NOT EXISTS saved_stocks (
    saved_stock_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    market VARCHAR(20),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_ticker UNIQUE (user_id, ticker)
);

-- 5. Research Tasks Table
CREATE TABLE IF NOT EXISTS research_tasks (
    task_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    market VARCHAR(20) NOT NULL,
    requested_period VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE
);
CREATE INDEX IF NOT EXISTS ix_research_tasks_task_id ON research_tasks(task_id);

-- 6. Research Reports Table
CREATE TABLE IF NOT EXISTS research_reports (
    report_id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) UNIQUE NOT NULL REFERENCES research_tasks(task_id) ON DELETE CASCADE,
    report_content TEXT NOT NULL,
    summary TEXT,
    limitations TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_research_reports_report_id ON research_reports(report_id);
```

### Step 6: Database Troubleshooting

| Error Message / Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `'psql' is not recognized as an internal or external command` | PostgreSQL `bin` directory is not in your Windows system PATH. | Add `C:\Program Files\PostgreSQL\16\bin` to Windows System Environment Variables $\rightarrow$ Path. Restart terminal. |
| `connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused` | PostgreSQL Windows service is stopped. | Run `Start-Service postgresql*` in an Administrator PowerShell, or open `services.msc` and start `postgresql-x64-16`. |
| `password authentication failed for user "postgres"` | Incorrect password entered or special characters in password not URL-encoded. | URL-encode special characters in `DATABASE_URL` (e.g. `@` becomes `%40`, `$` becomes `%24`). Test password by logging in with `psql -U postgres`. |
| `database "stock_analyst" does not exist` | Database has not yet been created in PostgreSQL. | Connect with `psql -U postgres` and run `CREATE DATABASE stock_analyst;`. |
| `Permission denied (0x0000271D/10013)` | Windows socket permissions or sandbox restriction blocking port 5432. | Ensure PostgreSQL is listening on `127.0.0.1` and Windows Firewall allows local inbound connections on port 5432. |

---

## 6. Environment Variables and Configuration

### Backend Environment Variables (`backend/.env`)

Create a `.env` file in the `backend/` directory:

```env
# ==============================================================================
# BACKEND CONFIGURATION (.env)
# ==============================================================================

# Database Connection String (PostgreSQL)
# Format: postgresql+psycopg2://<username>:<password>@<host>:<port>/<database_name>
# Note: If your password contains '@', encode it as '%40'.
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/stock_analyst

# Cryptographic Secret Key for JWT Signing
# Generate a random 64-character hex key with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=9a8d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e

# JWT Algorithm (Default: HS256)
ALGORITHM=HS256

# JWT Expiration in minutes (1440 = 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Inactivity Timeout in minutes (Sessions inactive for >15 mins are invalidated)
SESSION_INACTIVITY_MINUTES=15

# Session Cookie Name
SESSION_COOKIE_NAME=session_token

# Session Cookie Secure Flag (Set to False for localhost HTTP development; True for HTTPS production)
SESSION_COOKIE_SECURE=False

# Allowed CORS Origins (Comma-separated)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

### Frontend Environment Variables (`frontend/.env`)

Create a `.env` file in the `frontend/` directory:

```env
# ==============================================================================
# FRONTEND CONFIGURATION (.env)
# ==============================================================================

# Google OAuth 2.0 Client ID (Required for "Continue with Google" popup)
# Obtain from Google Cloud Console (APIs & Services > Credentials)
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# Backend API Base URL
# Left as '/api' because Vite dev server proxies '/api' directly to http://127.0.0.1:8000
VITE_API_URL=/api
```

### Obtaining a Google OAuth Client ID
To enable real Google Sign-In:
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `Stock-Research-Analyst`).
3. Go to **APIs & Services** $\rightarrow$ **OAuth consent screen**:
   - User Type: **External** $\rightarrow$ Click **Create**.
   - App Name: `Multi-Agent Stock Analyst`.
   - User Support Email & Developer Contact: Enter your email $\rightarrow$ Save and Continue.
4. Go to **APIs & Services** $\rightarrow$ **Credentials**:
   - Click **+ CREATE CREDENTIALS** $\rightarrow$ Select **OAuth client ID**.
   - Application type: **Web application**.
   - Name: `Stock Analyst Web Client`.
   - **Authorized JavaScript origins**:
     - `http://localhost:5173`
     - `http://127.0.0.1:5173`
     - `http://localhost:8000`
   - **Authorized redirect URIs**:
     - `http://localhost:5173`
     - `http://localhost:5173/login`
5. Click **Create** $\rightarrow$ Copy the generated **Client ID** (it ends with `.apps.googleusercontent.com`).
6. Paste it into `frontend/.env` as `VITE_GOOGLE_CLIENT_ID=...`.

---

## 7. Backend Setup and Execution

### Step 1: Open Terminal in `backend/`
```powershell
cd "c:\Users\Sahithi Redrouthu\OneDrive\Documents\infosys_spring_board\backend"
```

### Step 2: Create and Activate Python Virtual Environment
```powershell
# Create virtual environment named 'venv'
python -m venv venv

# Activate virtual environment on Windows
.\venv\Scripts\activate
```
*(Your prompt should now display `(venv)` at the beginning).*

### Step 3: Install Required Python Packages
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Database Connection with Database Inspector
Before launching the server, run the built-in database inspection utility to verify PostgreSQL connectivity:
```powershell
python ..\view_db.py
```
*You should see `Active URL: postgresql+psycopg2://...` and a list of database tables.*

### Step 5: Start the FastAPI Backend Server
```powershell
python run.py
```
Or directly with Uvicorn:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6: Verify Backend Execution
The terminal will display:
```text
INFO:     Will watch for changes in these directories: ['...\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [YYYY]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 8. Frontend Setup and Execution

### Step 1: Open a Second Terminal in `frontend/`
```powershell
cd "c:\Users\Sahithi Redrouthu\OneDrive\Documents\infosys_spring_board\frontend"
```

### Step 2: Install Node Dependencies
```powershell
npm install
```

### Step 3: Start the Vite Development Server
```powershell
npm run dev
```

### Step 4: Access the Application
The terminal will display:
```text
  VITE v6.1.0  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```
Open your browser and navigate to **[http://localhost:5173/](http://localhost:5173/)**.

### Step 5: Production Build (Optional)
To verify or compile the production bundle:
```powershell
npm run build
```
*(Assets compile to `frontend/dist/` in under 15 seconds).*

---

## 9. Complete API Documentation

Base URL: `http://127.0.0.1:8000` (or `/api` via Vite proxy).

### Authentication Endpoints

#### `POST /api/auth/register`
- **Purpose**: Registers a new user account and creates default user preferences.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "password": "Password123!",
    "confirm_password": "Password123!"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "created_at": "2026-11-14T10:00:00"
  }
  ```
- **Error Responses**: `400 Bad Request` (Email already registered), `422 Unprocessable Entity` (Password mismatch / weak password).

#### `POST /api/auth/login`
- **Purpose**: Authenticates credentials, creates a server-side session in PostgreSQL, and sets an HTTP-only cookie.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "email": "john.doe@example.com",
    "password": "Password123!"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "access_token": "a1b2c3d4e5f6...",
    "token_type": "bearer",
    "user": {
      "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "full_name": "John Doe",
      "email": "john.doe@example.com",
      "created_at": "2026-11-14T10:00:00"
    }
  }
  ```
  *Sets HTTP-only cookie: `session_token=<token>; Path=/; SameSite=Lax`.*
- **Error Responses**: `401 Unauthorized` (Incorrect email or password).

#### `POST /api/auth/google`
- **Purpose**: Authenticates or auto-registers a user via Google OAuth 2.0 ID token credential.
- **Authentication**: None.
- **Request Body**:
  ```json
  {
    "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6...",
    "email": "optional_override@gmail.com",
    "full_name": "Optional Name"
  }
  ```
- **Response (`200 OK`)**: Same schema as `POST /api/auth/login`. Sets session cookie.

#### `POST /api/auth/logout`
- **Purpose**: Invalidate active session in PostgreSQL and clear browser cookies.
- **Authentication**: Session cookie or `Authorization: Bearer <token>`.
- **Response (`200 OK`)**:
  ```json
  {
    "status": "ok",
    "message": "Session invalidated successfully."
  }
  ```

#### `GET /api/auth/me`
- **Purpose**: Returns the currently authenticated user's profile.
- **Authentication**: Required (`session_token` cookie or `Authorization: Bearer`).
- **Response (`200 OK`)**: `UserResponse` object.
- **Error Responses**: `401 Unauthorized` (Session missing, expired, or invalid).

---

### User Preferences Endpoints

#### `GET /api/preferences`
- **Purpose**: Fetches the authenticated user's workspace preferences.
- **Authentication**: Required.
- **Response (`200 OK`)**:
  ```json
  {
    "preference_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "preferred_market": "NASDAQ",
    "default_analysis_period": "1 Year",
    "updated_at": "2026-11-14T10:05:00"
  }
  ```

#### `PUT /api/preferences`
- **Purpose**: Updates the user's exchange market and default analysis period.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "preferred_market": "NSE",
    "default_analysis_period": "6 Months"
  }
  ```
  *Allowed markets: `NSE`, `BSE`, `NASDAQ`, `NYSE`. Allowed periods: `1 Month`, `3 Months`, `6 Months`, `1 Year`, `5 Years`.*
- **Response (`200 OK`)**: Updated `PreferenceResponse`.

---

### Watchlist & Company Autocomplete Endpoints

#### `GET /api/watchlist/companies`
- **Purpose**: Returns company suggestions strictly filtered by the selected exchange market and prefix.
- **Parameters**:
  - `market` (Query string, required): `NSE`, `BSE`, `NASDAQ`, or `NYSE`.
  - `q` (Query string, optional): Search prefix (case-insensitive).
- **Response (`200 OK`)**:
  ```json
  [
    {
      "ticker": "TATAMOTORS",
      "name": "Tata Motors Limited",
      "market": "NSE"
    },
    {
      "ticker": "TATASTEEL",
      "name": "Tata Steel Limited",
      "market": "NSE"
    }
  ]
  ```

#### `GET /api/watchlist`
- **Purpose**: Retrieves all stocks saved by the authenticated user, enriched with real-time Yahoo Finance market data.
- **Authentication**: Required.
- **Response (`200 OK`)**:
  ```json
  [
    {
      "saved_stock_id": "1a2b3c4d-...",
      "ticker": "INFY",
      "company_name": "Infosys Limited",
      "market": "NSE",
      "created_at": "2026-11-14T10:15:00",
      "last_price": 1824.50,
      "change": 14.20,
      "change_pct": 0.78,
      "currency": "INR"
    }
  ]
  ```

#### `POST /api/watchlist`
- **Purpose**: Adds a stock to the user's personal watchlist.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "market": "NASDAQ"
  }
  ```
- **Response (`201 Created`)**: Created `WatchlistItemResponse`.
- **Error Responses**: `400 Bad Request` ("AAPL is already present in your watchlist.").

#### `DELETE /api/watchlist/{stock_identifier}`
- **Purpose**: Removes a stock from the watchlist by ticker symbol or `saved_stock_id`.
- **Authentication**: Required.
- **Response (`204 No Content`)**: Empty response body.

---

### Stock Research Tasks & Reports Endpoints

#### `POST /api/tasks`
- **Purpose**: Creates a new stock research task initialized as `Pending` and enqueues an asynchronous background research pipeline.
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "market": "NASDAQ",
    "requested_period": "3 Months"
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "task_id": "4b5c6d7e-...",
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "market": "NASDAQ",
    "requested_period": "3 Months",
    "status": "Pending",
    "created_at": "2026-11-14T12:00:00",
    "completed_at": null
  }
  ```

#### `GET /api/tasks`
- **Purpose**: Returns the list of research tasks belonging strictly to the authenticated user.
- **Authentication**: Required.
- **Response (`200 OK`)**: List of `ResearchTaskResponse` objects.

#### `GET /api/tasks/{task_id}`
- **Purpose**: Retrieves the detailed equity research dossier for a specific research task.
- **Authentication**: Required (Enforces user ownership).
- **Response (`200 OK`)**:
  ```json
  {
    "task_id": "4b5c6d7e-...",
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "market": "NASDAQ",
    "requested_period": "3 Months",
    "status": "Completed",
    "created_at": "2026-11-14T12:00:00",
    "completed_at": "2026-11-14T12:00:03",
    "report": {
      "title": "Initial Stock Research Summary: NVDA (NASDAQ)",
      "period": "3 Months",
      "summary": "Dynamic market dataset retrieved from Yahoo Finance for NVDA (NASDAQ)...",
      "analyst_notes": "### Comprehensive Equity Research Dossier\n\n#### 1. Company & Asset Profile...",
      "limitations": "Historical price data subject to Yahoo Finance API query rate limits.",
      "metrics": {
        "market": "NASDAQ",
        "status": "Completed",
        "requested_period": "3 Months"
      }
    }
  }
  ```

#### `DELETE /api/tasks/{task_id}`
- **Purpose**: Permanently deletes an individual research entry and its associated report from the database.
- **Authentication**: Required (Strict ownership validation).
- **Response (`204 No Content`)**: Empty response body.

#### `PATCH /api/tasks/{task_id}/status`
- **Purpose**: Explicitly updates the research status of a task (`Pending`, `Processing`, `Completed`, `Failed`).
- **Authentication**: Required.
- **Request Body**:
  ```json
  {
    "status": "Completed"
  }
  ```
- **Response (`200 OK`)**: Updated `ResearchTaskResponse`.

---

### System & Health Endpoints

#### `GET /`
- **Purpose**: API metadata and documentation link.
- **Response (`200 OK`)**:
  ```json
  {
    "project": "Multi-Agent Stock Research Analyst",
    "module": "Module 1: User Authentication and Research Workspace",
    "status": "online",
    "docs_url": "/docs"
  }
  ```

#### `GET /health`
- **Purpose**: Liveness probe for load balancers and container orchestrators.
- **Response (`200 OK`)**: `{"status": "ok"}`

---

## 10. Google Authentication Integration

The application implements Google Sign-In via **Google Identity Services (GIS)**:

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant GIS as Google Identity Services (accounts.google.com)
    participant Front as React SPA (GoogleButton.jsx)
    participant Back as FastAPI (/api/auth/google)
    participant GoogleAPI as oauth2.googleapis.com
    participant DB as PostgreSQL

    User->>Front: Clicks "Continue with Google"
    Front->>GIS: Prompts Google Account Chooser
    User->>GIS: Selects Google Account & Authenticates
    GIS-->>Front: Returns Signed ID Token (JWT Credential)
    Front->>Back: POST /api/auth/google { credential }
    Back->>GoogleAPI: GET /tokeninfo?id_token={credential}
    GoogleAPI-->>Back: Cryptographic Verification (Email, Name, Sub)
    Back->>DB: Query or Auto-Register User & Default Preferences
    Back->>DB: Invalidate Old Sessions & Store New UserSession
    Back-->>Front: HTTP 200 + Set HTTP-Only Cookie (session_token)
    Front->>User: Redirects to Research Workspace Dashboard
```

### Key Technical Details
- **Google ID Token Verification**: The backend validates the cryptographic signature of the token against Google's public endpoints (`https://oauth2.googleapis.com/tokeninfo`).
- **Account Provisioning**: If a user logs in with Google for the first time, an account is automatically created in the `users` table and default preferences are initialized.
- **Account Chooser Notes**: Google's One Tap and Account Chooser UI is managed securely in an iframe by Google. If running in incognito or with third-party cookie restrictions, users select their account directly inside the popup.

---

## 11. Stock Research Workflow & Status Lifecycle

### The 4-Stage Status Lifecycle

```text
[ Pending ] ──────────► [ Processing ] ──────────► [ Completed ]
(Task created in DB)    (yfinance fetching       (Dossier compiled &
                         data & fundamentals)     persisted in DB)
                               │
                               ▼
                          [ Failed ]
                       (Symbol not found / API error)
```

1. **Pending (Blue Badge)**:
   - When the user clicks **"Start Research"** or **"▶ Research Now"**, the endpoint `POST /api/tasks` records the task in PostgreSQL with `status="Pending"` and returns `201 Created` immediately.
   - The frontend prepends the task to the Research History table, displaying the blue **Pending** badge.
2. **Processing (Pulsing Amber Badge)**:
   - A background task worker (`execute_research_pipeline`) begins execution asynchronously.
   - It updates the task status in PostgreSQL to `"Processing"`.
   - The frontend's reactive polling hook (`useEffect` in `DashboardPage.jsx`) automatically detects active tasks and polls `/api/tasks` every 1.2 seconds, switching the badge to pulsing amber.
3. **Completed (Emerald Badge)**:
   - The worker downloads historical prices, extracts valuation multiples (P/E, Forward P/E, EPS), calculates 50-day and 200-day moving averages, checks Wall Street consensus recommendations, and compiles the equity research dossier.
   - The dossier is saved to the `research_reports` table and the task status is marked `"Completed"`.
   - On the next poll, the UI renders the green **Completed** badge and polling gracefully stops.
4. **Failed (Rose Badge)**:
   - If an invalid ticker is provided or Yahoo Finance returns an error, the worker catches the exception, updates the status to `"Failed"`, logs the error message in the report, and alerts the user.

---

## 12. Research History Management

- **Viewing Tasks**: The **Research History** tab displays all historical tasks executed by the logged-in user, sorted by most recent first (`created_at DESC`).
- **Inspecting Reports**: Clicking **"View Report"** opens a modal displaying the complete Equity Research Dossier. Users can also click **"+ Add to Watchlist"** directly from inside the report modal.
- **Individual Deletion**: Every row includes a trash icon (`Trash2`). Clicking it opens a confirmation modal:
  > *"Are you sure you want to permanently delete the research task for AAPL (NASDAQ)? This action cannot be undone."*
- **Database Cascade**: Confirming deletion triggers `DELETE /api/tasks/{task_id}`, permanently removing the record from `research_tasks`. The related report in `research_reports` is removed automatically via foreign key cascade (`ON DELETE CASCADE`).
- **Watchlist Independence**: Deleting a research history entry does **not** delete or modify any corresponding entry in the user's watchlist.

---

## 13. Personal Stock Watchlist

- **Add to Watchlist**: Users can search for a company in the sidebar or Dedicated Watchlist tab and click **"+ Watchlist"**, or add a stock directly from an active research report dossier.
- **Duplicate Prevention**: Enforced at both the database level (`UniqueConstraint("user_id", "ticker")`) and backend router. Adding an existing stock returns `400 Bad Request` with an alert message.
- **Live Prices & Change**: On every watchlist fetch, the backend enriches saved tickers with live price quotes, day change, and percentage change using `yfinance`.
- **"▶ Research Now" Instant Trigger**: Clicking the play icon next to any watchlist item automatically:
  1. Sets the exchange market dropdown to the stock's market.
  2. Populates the company name input.
  3. Launches a research task immediately without manual re-typing.

---

## 14. Database Schema and Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ USER_SESSIONS : "has"
    USERS ||--o| USER_PREFERENCES : "configures"
    USERS ||--o{ SAVED_STOCKS : "monitors"
    USERS ||--o{ RESEARCH_TASKS : "initiates"
    RESEARCH_TASKS ||--o| RESEARCH_REPORTS : "produces"

    USERS {
        VARCHAR_36 user_id PK
        VARCHAR_255 full_name
        VARCHAR_255 email UK
        VARCHAR_255 password_hash
        TIMESTAMP created_at
    }

    USER_PREFERENCES {
        VARCHAR_36 preference_id PK
        VARCHAR_36 user_id FK,UK
        VARCHAR_20 preferred_market
        VARCHAR_20 default_analysis_period
        TIMESTAMP updated_at
    }

    USER_SESSIONS {
        VARCHAR_64 session_id PK
        VARCHAR_36 user_id FK
        TIMESTAMP created_at
        TIMESTAMP last_activity
        TIMESTAMP expires_at
        BOOLEAN is_active
    }

    SAVED_STOCKS {
        VARCHAR_36 saved_stock_id PK
        VARCHAR_36 user_id FK
        VARCHAR_20 ticker
        VARCHAR_255 company_name
        VARCHAR_20 market
        TIMESTAMP created_at
    }

    RESEARCH_TASKS {
        VARCHAR_36 task_id PK
        VARCHAR_36 user_id FK
        VARCHAR_20 ticker
        VARCHAR_255 company_name
        VARCHAR_20 market
        VARCHAR_20 requested_period
        VARCHAR_30 status
        TIMESTAMP created_at
        TIMESTAMP completed_at
    }

    RESEARCH_REPORTS {
        VARCHAR_36 report_id PK
        VARCHAR_36 task_id FK,UK
        TEXT report_content
        TEXT summary
        TEXT limitations
        TIMESTAMP created_at
    }
```

---

## 15. Zero-to-Running: Developer Execution Guide

### Quick-Start (Prerequisites Already Installed)

If you already have Python, Node.js, and PostgreSQL running:

```powershell
# 1. Start PostgreSQL Database
# (Ensure database 'stock_analyst' is created)

# 2. Start Backend (Terminal 1)
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python run.py

# 3. Start Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 4. Open Application
# Visit http://localhost:5173
```

---

### Detailed Step-by-Step Guide

#### Step 1: Clone the Repository
```powershell
git clone <repository-url>
cd infosys_spring_board
```

#### Step 2: Open in Visual Studio Code
```powershell
code .
```

#### Step 3: Configure PostgreSQL
Open PowerShell and create the application database:
```powershell
psql -U postgres -h localhost -c "CREATE DATABASE stock_analyst;"
```

#### Step 4: Configure Backend Environment Variables
Create `backend/.env` with your PostgreSQL password:
```powershell
# In backend/.env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/stock_analyst
SECRET_KEY=9a8d8e7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

#### Step 5: Install Backend Dependencies
Open **Terminal 1** in VS Code:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 6: Verify Database Connection
```powershell
python ..\view_db.py
```

#### Step 7: Start Backend Server
```powershell
python run.py
```
*Backend is now listening on `http://127.0.0.1:8000`.*

#### Step 8: Configure Frontend Environment Variables
Open a new **Terminal 2** in VS Code and verify `frontend/.env`:
```powershell
cd frontend
# Ensure frontend/.env contains:
# VITE_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
# VITE_API_URL=/api
```

#### Step 9: Install Frontend Dependencies & Start
In **Terminal 2**:
```powershell
npm install
npm run dev
```
*Frontend is now listening on `http://localhost:5173`.*

#### Step 10: Open Browser & Test Features
1. Open [http://localhost:5173/](http://localhost:5173/).
2. Click **"Register"** and create an account.
3. Test **Workspace Preferences**: Switch exchange market to **NSE** and period to **6 Months**. Click **Save**.
4. Test **Company Autocomplete**: In "Start New Research Task", type `TAT` $\rightarrow$ select `Tata Motors Limited`.
5. Click **"Start Research"** $\rightarrow$ Observe real-time status: **`Pending`** $\rightarrow$ **`Processing`** $\rightarrow$ **`Completed`**.
6. Click **"View Report"** $\rightarrow$ Inspect fundamental metrics and click **"+ Watchlist"**.
7. Navigate to the **Dedicated Watchlist** tab $\rightarrow$ Click **"▶ Research Now"**.

---

### One-Click Windows Launcher
On Windows, you can launch the entire stack (PostgreSQL verification, backend server, frontend server, and browser) with a single double-click on `start_app.bat`:
```powershell
.\start_app.bat
```

---

## 16. Automated Testing and Verification

The test suite thoroughly covers all Module 1 specifications:

### Run the Full Pytest Test Suite
```powershell
cd backend
$env:PYTHONPATH="."
.\venv\Scripts\python -m pytest tests/test_auth_and_workspace.py -v
```

### Run Feature-Specific Test Scripts
```powershell
cd backend
$env:PYTHONPATH="."

# 1. Test Session Management & 15-Minute Inactivity Auto-Logout
.\venv\Scripts\python tests/test_session_management.py

# 2. Test Strict Prefix Company Autocomplete & Exchange Isolation
.\venv\Scripts\python tests/test_company_autocomplete.py

# 3. Test Individual History Deletion, Status Progression & Watchlist Isolation
.\venv\Scripts\python tests/test_history_and_watchlist_features.py

# 4. Test End-to-End Tasks 4, 5, and 6 Verification
.\venv\Scripts\python tests/test_tasks_4_5_6.py
```

### Verification Results Summary
```text
============================================================
TEST SUMMARY
============================================================
test_auth_and_workspace.py               7/7 PASSED (100%)
test_session_management.py               8/8 PASSED (100%)
test_company_autocomplete.py             8/8 PASSED (100%)
test_history_and_watchlist_features.py   ALL PASSED (100%)
test_tasks_4_5_6.py                      ALL PASSED (100%)
frontend production build (vite build)   0 ERRORS   (100%)
============================================================
```

---

## 17. Security Architecture

1. **Bcrypt Password Hashing**: Passwords hashed with 12 salt rounds. Plaintext passwords are never logged or stored.
2. **Stateful Session Invalidation**: Active sessions are tracked in PostgreSQL (`user_sessions`). When a user clicks **Logout**, `is_active` is set to `False`, rendering existing tokens immediately unusable even if unexpired.
3. **HTTP-Only, SameSite Session Cookies**: Tokens are transmitted via `HttpOnly`, `SameSite=Lax` cookies, shielding authentication credentials from Cross-Site Scripting (XSS) and client-side extraction.
4. **15-Minute Inactivity Timeout**: The backend calculates `last_activity` against `SESSION_INACTIVITY_MINUTES`. Inactive sessions are revoked automatically upon the next API request.
5. **System / Server Restart Invalidation**: The server tracks `SERVER_BOOT_TIME`. Any sessions created prior to the server's boot timestamp are invalidated on system restarts.
6. **SQL Injection Prevention**: All database interactions use SQLAlchemy 2.0 parameterized queries and ORM mappings.
7. **Strict Multi-Tenant Isolation**: Endpoints derive the current user's ID exclusively from the verified backend session, preventing cross-user data leakage.
8. **Git Credential Safety**: Environment files (`.env`) and local databases (`*.db`) are strictly excluded from version control.

---

## 18. Troubleshooting Matrix

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **Port 8000 in use** | An existing Uvicorn or backend process is running. | Run `netstat -ano \| findstr :8000` to find the PID, then `taskkill /PID <PID> /F`. |
| **Port 5173 in use** | A prior Vite dev server process is still alive. | Stop the process or run `npx kill-port 5173`. |
| **PostgreSQL Connection Refused** | PostgreSQL service is stopped. | Run `Start-Service postgresql*` in PowerShell as Administrator. |
| **Authentication fails immediately after login** | Browser blocking cookies or clock mismatch. | Check browser cookie settings for `localhost`. Ensure system clock is synchronized. |
| **Yahoo Finance rate limit or data missing** | Ticker format unsupported or temporary rate limiting. | Verify ticker suffix format: `.NS` for NSE, `.BO` for BSE, bare symbol for NASDAQ/NYSE. |
| **Google Sign-In button displays warning** | `VITE_GOOGLE_CLIENT_ID` has not been set in `frontend/.env`. | Follow [Section 6](#obtaining-a-google-oauth-client-id) to obtain a client ID from Google Cloud Console. |

---

## 19. Contributing and Git Workflow

### 1. Branch Naming Conventions
- Feature: `feature/research-status-tracker`
- Bugfix: `fix/company-autocomplete-prefix`
- Documentation: `docs/readme-setup-guide`

### 2. Standard Workflow
```powershell
# 1. Fetch latest changes
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and verify tests pass
cd backend
.\venv\Scripts\python -m pytest tests/test_auth_and_workspace.py -v

# 4. Commit changes with a descriptive message
git add .
git commit -m "feat: implement real-time research task status tracking"

# 5. Push branch to GitHub
git push -u origin feature/your-feature-name

# 6. Open Pull Request on GitHub
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.
