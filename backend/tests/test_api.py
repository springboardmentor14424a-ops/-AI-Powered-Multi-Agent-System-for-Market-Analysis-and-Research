from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_and_root():
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["message"] == "StockMind AI API is running"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}


def test_register_login_and_me():
    # Register
    reg_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Investor",
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["message"] == "User registered successfully"
    assert reg_data["user"]["email"] == "alice@example.com"
    assert reg_data["user"]["full_name"] == "Alice Investor"
    assert "hashed_password" not in reg_data["user"]

    # Duplicate registration should fail
    dup_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alice Two",
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "Email already registered"

    # Wrong password
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # Valid login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["token_type"] == "bearer"
    token = login_data["access_token"]
    assert token

    # /api/auth/me with valid token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "alice@example.com"

    # /api/auth/me without token
    no_auth = client.get("/api/auth/me")
    assert no_auth.status_code in (401, 403)

    # /api/auth/me with invalid token
    bad_auth = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert bad_auth.status_code == 401


@patch("app.services.stock_service.yf.Search")
def test_stock_search(mock_search):
    mock_instance = MagicMock()
    mock_instance.quotes = [
        {
            "symbol": "AAPL",
            "shortname": "Apple Inc.",
            "exchange": "NMS",
            "quoteType": "EQUITY",
        }
    ]
    mock_search.return_value = mock_instance

    res = client.get("/api/stocks/search?q=AAPL")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["name"] == "Apple Inc."


@patch("app.services.stock_service.yf.Ticker")
def test_stock_history_and_quote(mock_ticker):
    dates = pd.to_datetime(["2026-01-02", "2026-01-03"])
    df = pd.DataFrame(
        {
            "Open": [180.0, 182.5],
            "High": [183.0, 185.0],
            "Low": [179.0, 181.0],
            "Close": [182.0, 184.5],
            "Volume": [50000000, 48000000],
        },
        index=dates,
    )
    ticker_instance = MagicMock()
    ticker_instance.history.return_value = df
    ticker_instance.info = {
        "shortName": "Apple Inc.",
        "currentPrice": 184.5,
        "previousClose": 182.0,
        "marketCap": 2850000000000,
        "volume": 48000000,
        "exchange": "NMS",
        "currency": "USD",
    }
    mock_ticker.return_value = ticker_instance

    hist_res = client.get("/api/stocks/AAPL/history?period=1mo&interval=1d")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) == 2
    assert hist_data[0]["date"] == "2026-01-02"
    assert hist_data[1]["close"] == 184.5

    quote_res = client.get("/api/stocks/AAPL/quote")
    assert quote_res.status_code == 200
    quote_data = quote_res.json()
    assert quote_data["symbol"] == "AAPL"
    assert quote_data["price"] == 184.5
    assert quote_data["market_cap"] == 2850000000000

