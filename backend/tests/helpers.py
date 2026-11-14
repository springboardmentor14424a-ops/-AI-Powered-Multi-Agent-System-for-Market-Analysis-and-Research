"""Synthetic market data for tests (no network needed)."""
import numpy as np
import pandas as pd

from app.data import fundamentals as _fundamentals
from app.data import news as _news
from app.data import prices as _prices
from app.data.fundamentals import Fundamentals
from app.data.macro import VolIndex
from app.data.news import NewsData
from app.data.prices import PriceData

# The autouse fixture in conftest.py replaces the data providers with fakes. These are
# the real functions, captured at import time (before any fixture runs), for loader tests.
REAL_GET_PRICES = _prices.get_prices
REAL_GET_NEWS = _news.get_news
REAL_GET_FUNDAMENTALS = _fundamentals.get_fundamentals


def make_prices(n=900, drift=0.0004, sigma=0.015, seed=1, symbol="TEST", source="synthetic") -> PriceData:
    rng = np.random.RandomState(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, sigma, n)))
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    df = pd.DataFrame(
        {"open": close, "high": close * 1.01, "low": close * 0.99, "close": close, "volume": 1e6}, index=idx
    )
    return PriceData(df, symbol, source)


def trend_prices(up: bool, n=400) -> PriceData:
    """Smooth, near-noiseless trend so the technical rules have an unambiguous answer."""
    rng = np.random.RandomState(3)
    step = 0.002 if up else -0.002
    close = 100 * np.exp(np.cumsum(np.full(n, step) + rng.normal(0, 0.002, n)))
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    df = pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1e6}, index=idx)
    return PriceData(df, "TREND", "synthetic")


def make_news(titles, end=None) -> NewsData:
    end = end or pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end, periods=len(titles), freq="D")
    return NewsData(pd.DataFrame({"date": dates, "title": titles}), ["synthetic news"])


POSITIVE = [f"Company beats estimates as profit surges to a record high #{i}" for i in range(8)]
NEGATIVE = [f"Shares plunge after lawsuit and profit warning, analysts downgrade #{i}" for i in range(8)]


def make_fundamentals(**metrics) -> Fundamentals:
    base = {"revenue_growth": 0.12, "net_margin": 0.20, "roe": 0.25, "liabilities_to_assets": 0.5}
    base.update(metrics)
    return Fundamentals(base, "synthetic fundamentals", "2025-09-30")


def make_vol_index(name="VIX", latest=15.0, percentile=0.2) -> VolIndex:
    return VolIndex(name, latest, percentile, "2026-11-12", "synthetic")
