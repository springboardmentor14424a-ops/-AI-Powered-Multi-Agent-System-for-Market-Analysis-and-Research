-- Module 1 schema (PostgreSQL). The backend also creates these tables automatically on startup
-- via SQLAlchemy; this file documents the structure and can be run manually if preferred.

CREATE TABLE users (
    user_id        SERIAL PRIMARY KEY,
    full_name      VARCHAR(100)  NOT NULL,
    email          VARCHAR(255)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255)  NOT NULL,          -- bcrypt hash, never the password
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE user_preferences (
    user_id          INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    market           VARCHAR(10) NOT NULL DEFAULT 'NASDAQ'
                     CHECK (market IN ('NSE','BSE','NASDAQ','NYSE')),
    analysis_period  VARCHAR(5)  NOT NULL DEFAULT '1Y'
                     CHECK (analysis_period IN ('1M','3M','6M','1Y','5Y')),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE saved_stocks (
    saved_stock_id  SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker          VARCHAR(20)  NOT NULL,
    company_name    VARCHAR(150) NOT NULL,
    market          VARCHAR(10)  NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_saved_stock_user_ticker UNIQUE (user_id, ticker)   -- no duplicates per user
);
CREATE INDEX ix_saved_stocks_user_id ON saved_stocks(user_id);

CREATE TABLE research_tasks (
    task_id          SERIAL PRIMARY KEY,
    user_id          INTEGER      NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ticker           VARCHAR(20)  NOT NULL,
    company_name     VARCHAR(150) NOT NULL,
    market           VARCHAR(10)  NOT NULL,
    analysis_period  VARCHAR(5)   NOT NULL,
    status           VARCHAR(20)  NOT NULL DEFAULT 'Pending'
                     CHECK (status IN ('Pending','Processing','Completed','Failed')),
    report           TEXT,
    error_message    TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ
);
CREATE INDEX ix_research_tasks_user_created ON research_tasks(user_id, created_at);
