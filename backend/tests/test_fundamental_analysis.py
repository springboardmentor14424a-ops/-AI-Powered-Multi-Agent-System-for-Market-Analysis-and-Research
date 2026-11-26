from datetime import datetime

import pandas as pd
from fastapi.testclient import TestClient

from app import fundamental_analysis
from app import market_data
from app.main import app

client = TestClient(app)


class FakeTicker:
    def __init__(self, info, financials, balance_sheet, cashflow, history):
        self._info = info
        self.financials = financials
        self.balance_sheet = balance_sheet
        self.cashflow = cashflow
        self._history = history

    def get_info(self):
        return self._info

    def history(self, period, auto_adjust):
        return self._history


def _history():
    return pd.DataFrame(
        [
            {
                "Open": 19.0,
                "High": 21.0,
                "Low": 18.0,
                "Close": 20.0,
                "Volume": 1000,
            }
        ],
        index=pd.to_datetime(["2025-01-02"]),
    )


def _statement(rows):
    return pd.DataFrame.from_dict(
        rows,
        orient="index",
        columns=pd.to_datetime(["2024-12-31", "2023-12-31"]),
    )


def test_fundamental_analysis_calculates_growth_and_includes_source(monkeypatch):
    stock = FakeTicker(
        {
            "shortName": "Example Corp",
            "currency": "USD",
            "exchangeName": "Nasdaq",
            "marketCap": 1000,
            "currentPrice": 20,
            "trailingPE": 10,
            "priceToBook": 2,
            "returnOnEquity": 0.15,
            "profitMargins": 0.1,
            "operatingMargins": 0.2,
            "debtToEquity": 25,
            "currentRatio": 1.5,
        },
        _statement({"Total Revenue": [120, 100], "Net Income": [30, 20]}),
        _statement({
            "Total Debt": [40, 50],
            "Cash And Cash Equivalents": [10, 20],
            "Stockholders Equity": [100, 100],
        }),
        pd.DataFrame(),
        _history(),
    )
    monkeypatch.setattr(fundamental_analysis.yf, "Ticker", lambda ticker: stock)

    result = fundamental_analysis.run_fundamental_analysis("exmp")

    assert result.ticker == "EXMP"
    assert result.metrics.revenue_growth_percent == 20
    assert result.metrics.net_income_growth_percent == 50
    assert result.metrics.return_on_equity_percent == 15
    assert result.metrics.net_debt == 30
    assert result.historical_financials[0].total_debt == 40
    assert result.market_data.prices[0].close == 20
    assert result.source.provider == "Yahoo Finance via yfinance"
    assert result.source.url.endswith("/EXMP/")


def test_fundamental_analysis_reports_missing_financials(monkeypatch):
    stock = FakeTicker({}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), _history())
    monkeypatch.setattr(fundamental_analysis.yf, "Ticker", lambda ticker: stock)

    result = fundamental_analysis.run_fundamental_analysis("EXMP")

    assert result.findings
    assert "No annual financial statements were available." in result.data_gaps
    assert result.metrics.trailing_pe is None


def test_fundamental_analysis_calculates_ratios_when_yahoo_does_not_provide_them(monkeypatch):
    stock = FakeTicker(
        {"shortName": "Example Corp", "marketCap": 1000, "currentPrice": 20, "trailingEps": 2},
        _statement({"Total Revenue": [200, 100], "Net Income": [20, 10]}),
        _statement({"Total Debt": [50, 50], "Stockholders Equity": [100, 100]}),
        pd.DataFrame(),
        _history(),
    )
    monkeypatch.setattr(fundamental_analysis.yf, "Ticker", lambda ticker: stock)

    result = fundamental_analysis.run_fundamental_analysis("EXMP")

    assert result.metrics.trailing_pe == 10
    assert result.metrics.price_to_book == 10
    assert result.metrics.return_on_equity_percent == 20
    assert result.metrics.debt_to_equity_percent == 50
    assert result.metrics.profit_margin_percent == 10


def test_stock_search_returns_distinct_yfinance_tickers(monkeypatch):
    class FakeSearch:
        quotes = [
            {"symbol": "EXMP", "shortname": "Example Corp", "exchange": "NMS", "quoteType": "EQUITY"},
            {"symbol": "EXMP", "shortname": "Example Corp", "exchange": "NMS", "quoteType": "EQUITY"},
        ]

    monkeypatch.setattr(market_data.yf, "Search", lambda *args, **kwargs: FakeSearch())

    result = market_data.search_stocks("Example")

    assert len(result.results) == 1
    assert result.results[0].ticker == "EXMP"
    assert result.results[0].name == "Example Corp"
    assert result.source == "Yahoo Finance via yfinance"


def test_stock_search_filters_results_for_selected_indian_market(monkeypatch):
    class FakeSearch:
        quotes = [
            {"symbol": "EXMP", "shortname": "Example US", "exchange": "NMS", "quoteType": "EQUITY"},
            {"symbol": "EXMP.NS", "shortname": "Example India", "exchange": "NSI", "quoteType": "EQUITY"},
        ]

    monkeypatch.setattr(market_data.yf, "Search", lambda *args, **kwargs: FakeSearch())

    result = market_data.search_stocks("Example", market="NSE")

    assert result.market == "NSE"
    assert [item.ticker for item in result.results] == ["EXMP.NS"]


def test_market_specific_ticker_normalization():
    assert market_data.normalize_ticker("reliance", "NSE") == "RELIANCE.NS"
    assert market_data.normalize_ticker("reliance", "BSE") == "RELIANCE.BO"
    try:
        market_data.normalize_ticker("RELIANCE.NS", "BSE")
    except ValueError as error:
        assert "NSE ticker" in str(error)
    else:
        raise AssertionError("Mismatched exchange suffix should be rejected")


def test_fundamental_analysis_compares_same_industry_peers(monkeypatch):
    target = FakeTicker(
        {"shortName": "Example Corp", "industry": "Software", "sector": "Technology"},
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        _history(),
    )
    peer = FakeTicker(
        {
            "shortName": "Peer Corp",
            "industry": "Software",
            "trailingPE": 12,
            "priceToBook": 3,
            "returnOnEquity": 0.2,
        },
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        _history(),
    )

    class FakeSearch:
        quotes = [{"symbol": "PEER", "exchange": "NMS", "quoteType": "EQUITY"}]

    monkeypatch.setattr(fundamental_analysis.yf, "Ticker", lambda ticker: target if ticker == "EXMP" else peer)
    monkeypatch.setattr(fundamental_analysis.yf, "Search", lambda *args, **kwargs: FakeSearch())

    result = fundamental_analysis.run_fundamental_analysis("EXMP")

    assert result.industry == "Software"
    assert len(result.peer_comparisons) == 1
    assert result.peer_comparisons[0].ticker == "PEER"
    assert result.peer_comparisons[0].return_on_equity_percent == 20


def test_market_data_excludes_invalid_prices_and_reports_duplicate_dates(monkeypatch):
    prices = pd.DataFrame(
        [
            {"Open": 10, "High": 12, "Low": 9, "Close": 11, "Volume": 100},
            {"Open": 10, "High": 12, "Low": 9, "Close": 11, "Volume": 100},
            {"Open": 10, "High": 8, "Low": 9, "Close": 11, "Volume": 100},
        ],
        index=pd.to_datetime(["2025-01-02", "2025-01-02", "2025-01-03"]),
    )
    stock = FakeTicker({"shortName": "Example Corp"}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), prices)
    monkeypatch.setattr(fundamental_analysis.yf, "Ticker", lambda ticker: stock)

    result = fundamental_analysis.run_fundamental_analysis("EXMP")

    assert len(result.market_data.prices) == 1
    assert any("duplicate price date" in warning for warning in result.market_data.warnings)


def test_stock_research_endpoints_require_authentication():
    response = client.get("/api/stocks/search", params={"q": "Apple"})
    assert response.status_code == 401


def test_financial_periods_use_latest_statement_dates():
    periods = fundamental_analysis._financial_periods(
        _statement({"Total Revenue": [120, 100]}),
        _statement({"Stockholders Equity": [80, 70]}),
        pd.DataFrame(),
    )

    assert periods[0].period == datetime(2024, 12, 31).date().isoformat()
    assert periods[0].revenue == 120
