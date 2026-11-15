# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# Multi-Agent Stock Research Analyst - Module 1
## User Authentication and Research Workspace

This project is a full-stack stock research application built with a **FastAPI** backend, a **React (Vite)** frontend, and a relational database managed via **SQLAlchemy**. It features secure **Google OAuth 2.0 authentication**, real-time market data fetching via **`yfinance`**, a persistent user watchlist, and customizable research preferences.

---

## Prerequisites
Before running this application, ensure your system has the following installed:
**Python** (v3.9 or higher)
**Node.js** (v16 or higher) & npm
 A **Google Cloud Console Project** with OAuth 2.0 credentials configured (Redirect URI: `http://localhost:8001/auth/google/callback`)

---

## Environment Variables
Create a `.env` file in the root backend directory with the following variables:

env
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
SECRET_KEY=your_jwt_secret_key_here
DATABASE_URL=sqlite:///./stock_research.db