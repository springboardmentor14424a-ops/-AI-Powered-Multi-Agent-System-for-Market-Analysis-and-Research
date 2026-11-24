import numpy as np
import pandas as pd
import pytest

from app.services import market_data
from app.services.market_data import NoDataError


def test_symbol_conversion():
    assert market_data.to_yahoo_symbol("tcs", "NSE") == "TCS.NS"
    assert market_data.to_yahoo_symbol("TCS", "BSE") == "TCS.BO"
    assert market_data.to_yahoo_symbol("aapl", "NASDAQ") == "AAPL"
    assert market_data.to_yahoo_symbol("IBM", "NYSE") == "IBM"
    assert market_data.to_yahoo_symbol("TCS.NS", "NSE") == "TCS.NS"
    assert market_data.to_yahoo_symbol("RELIANCE.BO", "NSE") == "RELIANCE.BO"


def make_fake_ticker(df):
    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None, auto_adjust=False):
            return df

    return FakeTicker


def test_validation_cleans_bad_rows(monkeypatch):
    market_data._cache.clear()
    index = pd.DatetimeIndex(
        ["2026-01-05", "2026-01-06", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09"],
        name="Date",
    )
    df = pd.DataFrame(
        {
            "Open": [10, 11, 11, 12, 13, 14],
            "High": [11, 12, 12, 13, 12, 15],
            "Low": [9, 10, 10, 11, 13, 13],
            "Close": [10.5, 11.5, 11.6, np.nan, 12.5, 14.5],
            "Volume": [100, 200, 200, 300, 400, 500],
        },
        index=index,
    )
    monkeypatch.setattr(market_data.yf, "Ticker", make_fake_ticker(df))

    result = market_data.fetch_history("TEST", "NASDAQ", "1M")

    assert result["validation"] == {
        "rows_received": 6,
        "rows_returned": 3,
        "duplicates_removed": 1,
        "missing_removed": 1,
        "inconsistent_removed": 1,
    }
    assert [p["date"] for p in result["prices"]] == ["2026-01-05", "2026-01-06", "2026-01-09"]
    assert result["prices"][1]["close"] == 11.6


def test_empty_data_raises(monkeypatch):
    market_data._cache.clear()
    monkeypatch.setattr(market_data.yf, "Ticker", make_fake_ticker(pd.DataFrame()))
    with pytest.raises(NoDataError):
        market_data.fetch_history("NOPE", "NASDAQ", "1M")