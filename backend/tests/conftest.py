import os

# Must be set before the app is imported.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-bytes-long"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["COOKIE_SECURE"] = "false"  # TestClient talks plain http

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

import helpers
from app.config import settings
from app.database import Base, engine
from app.deps import get_current_user
from app.main import app


# A protected, state-changing route so CSRF handling can be tested.
@app.post("/api/_test/echo")
def _echo(user=Depends(get_current_user)):
    return {"id": user.id}


@pytest.fixture(autouse=True)
def isolated_data(monkeypatch, tmp_path):
    """Every test gets an empty data folder and synthetic data providers, so nothing
    touches the network or the real backend/data folder."""
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(settings, "SEC_USER_AGENT", "")
    from app.stocks import provider_symbol

    monkeypatch.setattr(
        "app.data.prices.get_prices",
        lambda market, ticker, days: helpers.make_prices(symbol=provider_symbol(market, ticker)),
    )
    monkeypatch.setattr("app.data.prices.get_benchmark", lambda market, days: helpers.make_prices(seed=9, symbol="^BENCH"))
    monkeypatch.setattr(
        "app.data.news.get_news",
        lambda market, ticker, company: helpers.make_news(helpers.POSITIVE + helpers.NEGATIVE[:3]),
    )
    monkeypatch.setattr("app.data.fundamentals.get_fundamentals", lambda market, ticker: helpers.make_fundamentals())
    monkeypatch.setattr("app.data.macro.get_volatility_index", lambda market: helpers.make_vol_index())
    from app.data import sentiment_model

    sentiment_model.reset_model_cache()


@pytest.fixture()
def client():
    with TestClient(app) as c:  # runs lifespan -> creates tables
        yield c
    Base.metadata.drop_all(bind=engine)
