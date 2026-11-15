-- ============================================================
-- Multi-Agent Stock Research Analyst Platform
-- PostgreSQL Schema
-- ============================================================

-- ----------------------------------------------------------------
-- 1. users
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    full_name     VARCHAR(255),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id     VARCHAR(255) UNIQUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ----------------------------------------------------------------
-- 2. research_tasks
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_tasks (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE,
    company_name    VARCHAR(255) NOT NULL,
    ticker          VARCHAR(50)  NOT NULL,
    market          VARCHAR(50)  NOT NULL,
    analysis_period VARCHAR(50)  NOT NULL,
    status          VARCHAR(20)  DEFAULT 'Pending'
                    CHECK (status IN ('Pending', 'Processing', 'Completed', 'Failed')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_tasks_user_id ON research_tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_research_tasks_ticker  ON research_tasks (ticker);

-- ----------------------------------------------------------------
-- 3. research_reports
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_reports (
    id             SERIAL PRIMARY KEY,
    task_id        INT REFERENCES research_tasks(id) ON DELETE CASCADE,
    report_content TEXT,
    generated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_reports_task_id ON research_reports (task_id);

-- ----------------------------------------------------------------
-- 4. saved_stocks
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS saved_stocks (
    id           SERIAL PRIMARY KEY,
    user_id      INT REFERENCES users(id) ON DELETE CASCADE,
    ticker       VARCHAR(50)  NOT NULL,
    company_name VARCHAR(255),
    market       VARCHAR(50),
    added_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_saved_stocks_user_id ON saved_stocks (user_id);
CREATE INDEX IF NOT EXISTS idx_saved_stocks_ticker  ON saved_stocks (ticker);

-- ----------------------------------------------------------------
-- 5. user_preferences
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    market          VARCHAR(50) DEFAULT 'NASDAQ',
    analysis_period VARCHAR(50) DEFAULT '1 Year',
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences (user_id);
