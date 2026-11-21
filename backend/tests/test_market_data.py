import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

import helpers
from app.data import DataUnavailable, company, prices, validation
from app.data.search import quote_to_stock
from app.database import SessionLocal
from app.models import DataRetrieval
from test_workspace import sign_up_and_in


def frame(n=30, **over):
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    c = np.linspace(100, 110, n)
    df = pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c, "volume": 1000.0}, index=idx)
    for k, v in over.items():
        df[k] = v
    return df


def check(report, id_):
    return next(c for c in report["checks"] if c["id"] == id_)


# ---------------- validation ----------------

def test_clean_frame_passes_every_check():
    r = validation.validate_prices(frame())
    assert r["status"] == "ok" and r["rows"] == 30
    assert all(c["passed"] for c in r["checks"])


def test_clean_reports_duplicates_and_missing_close():
    raw = frame(5)
    raw = pd.concat([raw, raw.iloc[[2]]])  # a duplicated date
    raw.iloc[1, raw.columns.get_loc("close")] = np.nan
    out = prices._clean(raw)
    assert out.attrs["cleaning"] == {"raw_rows": 6, "duplicate_dates_removed": 1, "rows_without_close_removed": 1}
    r = validation.validate_prices(out, out.attrs["cleaning"])
    assert check(r, "duplicate_dates")["count"] == 1 and not check(r, "duplicate_dates")["passed"]
    assert check(r, "missing_values")["count"] == 1


def test_missing_cells_are_flagged():
    df = frame()
    df.iloc[4, df.columns.get_loc("volume")] = np.nan
    r = validation.validate_prices(df)
    assert check(r, "missing_values")["count"] == 1
    assert list(r["flagged"].values()) == ["missing value"]


def test_inconsistent_prices_are_errors():
    df = frame()
    df.iloc[3, df.columns.get_loc("high")] = 50   # high below low
    df.iloc[7, df.columns.get_loc("close")] = -1  # negative price
    r = validation.validate_prices(df)
    c = check(r, "inconsistent_prices")
    assert c["severity"] == "error" and c["count"] == 2 and len(c["examples"]) == 2
    assert r["status"] == "errors"


def test_negative_volume_gaps_extreme_moves_and_stale():
    df = frame()
    df.iloc[2, df.columns.get_loc("volume")] = -5
    r = validation.validate_prices(df)
    assert check(r, "negative_volume")["count"] == 1

    gap = pd.concat([frame(10).iloc[:5], frame(10).iloc[5:].set_axis(frame(10).index[5:] + pd.Timedelta(days=20))])
    assert check(validation.validate_prices(gap), "date_gaps")["count"] == 1

    jump = frame()
    jump.iloc[10:, jump.columns.get_loc("close")] *= 1.6
    jump["high"] = jump["close"] * 1.01
    jump["low"] = jump["close"] * 0.99
    jump["open"] = jump["close"]
    assert check(validation.validate_prices(jump), "extreme_moves")["count"] == 1

    old = frame()
    old.index = old.index - pd.Timedelta(days=60)
    assert not check(validation.validate_prices(old), "stale")["passed"]
    fut = validation.validate_prices(frame(), today=date.today() - timedelta(days=5))
    assert check(fut, "future_dates")["count"] >= 1


# ---------------- provenance + cache ----------------

def test_retrieval_time_and_source_survive_the_cache(monkeypatch):
    raw = pd.concat([frame(40), frame(40).iloc[[3]]])
    monkeypatch.setattr(prices, "fetch_live", lambda symbol, need: prices._clean(raw))
    first = helpers.REAL_GET_PRICES("NASDAQ", "AAPL", 90)
    assert not first.from_cache and first.source == "Yahoo Finance (yfinance)"
    assert first.retrieved_at.endswith("Z") and first.cleaning["duplicate_dates_removed"] == 1

    monkeypatch.setattr(prices, "fetch_live", lambda *a: (_ for _ in ()).throw(AssertionError("must use cache")))
    second = helpers.REAL_GET_PRICES("NASDAQ", "AAPL", 90)
    assert second.from_cache and second.retrieved_at == first.retrieved_at
    assert second.cleaning["duplicate_dates_removed"] == 1


# ---------------- search ----------------

def test_quote_mapping():
    assert quote_to_stock({"symbol": "INFY.NS", "shortname": "Infosys", "quoteType": "EQUITY"})["market"] == "NSE"
    assert quote_to_stock({"symbol": "500209.BO", "longname": "Infosys Ltd", "quoteType": "EQUITY"})["ticker"] == "500209"
    assert quote_to_stock({"symbol": "ZM", "shortname": "Zoom", "exchange": "NMS"})["market"] == "NASDAQ"
    assert quote_to_stock({"symbol": "X", "shortname": "X", "exchange": "NYQ"})["market"] == "NYSE"
    assert quote_to_stock({"symbol": "BTC-USD", "shortname": "Bitcoin", "quoteType": "CRYPTOCURRENCY"}) is None
    assert quote_to_stock({"symbol": "VOD.L", "shortname": "Vodafone", "exchange": "LSE"}) is None


def test_search_merges_builtin_and_live_without_duplicates(client, monkeypatch):
    sign_up_and_in(client, "s@example.com")
    live = [
        {"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ", "provider_symbol": "AAPL"},
        {"ticker": "APLE", "company_name": "Apple Hospitality REIT", "market": "NYSE", "provider_symbol": "APLE"},
    ]
    monkeypatch.setattr("app.routers.market_data.live_search", lambda q, m=None: live)
    r = client.get("/api/market/search", params={"q": "apple"}).json()
    assert [(s["ticker"], s["source"]) for s in r] == [("AAPL", "Built-in stock list"), ("APLE", "Yahoo Finance search")]


def test_search_still_works_when_live_search_is_down(client, monkeypatch):
    sign_up_and_in(client, "s@example.com")
    monkeypatch.setattr("app.routers.market_data.live_search", lambda q, m=None: [])
    assert client.get("/api/market/search", params={"q": "infosys", "market": "NSE"}).json()[0]["ticker"] == "INFY"


def test_market_data_requires_login(client):
    for path in ("/search?q=a", "/NSE/TCS/prices", "/NSE/TCS/profile", "/NSE/TCS/financials", "/retrievals"):
        assert client.get("/api/market" + path).status_code == 401


# ---------------- prices endpoint ----------------

def test_prices_return_ohlcv_with_source_timestamp_and_quality(client):
    sign_up_and_in(client, "p@example.com")
    r = client.get("/api/market/NSE/TCS/prices", params={"period": "3 months"})
    assert r.status_code == 200
    d = r.json()
    assert set(d["rows"][0]) == {"date", "open", "high", "low", "close", "volume", "flag"}
    assert d["provenance"]["symbol"] == "TCS.NS" and d["provenance"]["source"] == "synthetic"
    assert d["company_name"] == "Tata Consultancy Services Limited"
    assert d["quality"]["status"] in {"ok", "warnings"} and "flagged" not in d["quality"]
    assert d["rows"][0]["date"] >= (date.today() - timedelta(days=92)).isoformat()
    assert len(d["rows"]) == d["provenance"]["rows"]


def test_longer_period_returns_more_rows(client):
    sign_up_and_in(client, "p@example.com")
    n = lambda p: len(client.get("/api/market/NASDAQ/AAPL/prices", params={"period": p}).json()["rows"])
    assert n("1 month") < n("1 year") < n("5 years")


def test_bad_ticker_or_market_is_rejected(client):
    sign_up_and_in(client, "p@example.com")
    assert client.get("/api/market/BSE/RELIANCE/prices").status_code == 422   # BSE needs a 6-digit code
    assert client.get("/api/market/LSE/VOD/prices").status_code == 422
    assert client.get("/api/market/NSE/TCS/prices", params={"period": "forever"}).status_code == 422


def test_provider_failure_is_a_clean_503(client, monkeypatch):
    sign_up_and_in(client, "p@example.com")

    def boom(*a):
        raise DataUnavailable("Could not download prices for TCS.NS from Yahoo Finance (offline or blocked).")

    monkeypatch.setattr("app.data.prices.get_prices", boom)
    r = client.get("/api/market/NSE/TCS/prices")
    assert r.status_code == 503 and "Yahoo Finance" in r.json()["detail"]


def test_flagged_rows_are_marked_in_the_response(client, monkeypatch):
    sign_up_and_in(client, "p@example.com")
    bad = helpers.make_prices(n=60)
    bad.frame.iloc[-3, bad.frame.columns.get_loc("high")] = 1.0
    monkeypatch.setattr("app.data.prices.get_prices", lambda m, t, d: bad)
    d = client.get("/api/market/NASDAQ/AAPL/prices", params={"period": "1 month"}).json()
    assert d["quality"]["status"] == "errors"
    assert [r["flag"] for r in d["rows"] if r["flag"]] == ["high is below low"]


# ---------------- profile + financials ----------------

def test_profile_from_provider_and_fallback(client, monkeypatch):
    sign_up_and_in(client, "c@example.com")
    full = {k: None for k in company.PROFILE_FIELDS} | {"name": "Tata Consultancy Services", "sector": "Technology"}
    monkeypatch.setattr(company, "_yf_profile", lambda s: full)
    d = client.get("/api/market/NSE/TCS/profile").json()
    assert d["profile"]["sector"] == "Technology" and d["provenance"]["source"] == "Yahoo Finance (yfinance)"
    assert any("Not available from the source" in n for n in d["notes"])

    def down(s):
        raise DataUnavailable("Could not download the company profile from Yahoo Finance.")

    monkeypatch.setattr(company, "_yf_profile", down)
    d = client.get("/api/market/NSE/INFY/profile").json()
    assert d["provenance"]["source"] == "Built-in stock list" and d["profile"]["name"] == "Infosys Limited"
    assert client.get("/api/market/NSE/NOSUCHCO/profile").status_code == 503


def test_statement_frame_conversion():
    cols = [pd.Timestamp("2024-03-31"), pd.Timestamp("2025-03-31")]
    df = pd.DataFrame({cols[0]: [100.0, np.nan], cols[1]: [120.0, np.nan]}, index=["Total Revenue", "Net Income"])
    periods, rows = company._frame_to_rows(df, company._INCOME)
    assert periods == ["2025-03-31", "2024-03-31"]
    assert rows == [{"item": "Total revenue", "values": [120.0, 100.0]}]  # all-NaN row skipped
    assert company._frame_to_rows(None, company._INCOME) == ([], [])


def test_statements_from_sec_facts():
    def entry(end, val, start=None):
        e = {"end": end, "val": val, "fp": "FY", "form": "10-K", "filed": end}
        if start:
            e["start"] = start
        return e

    facts = {"facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [entry("2024-12-31", 10, "2024-01-01"), entry("2023-12-31", 8, "2023-01-01")]}},
        "NetIncomeLoss": {"units": {"USD": [entry("2024-12-31", 2, "2024-01-01")]}},
        "Assets": {"units": {"USD": [entry("2024-12-31", 50), entry("2023-12-31", 40)]}},
    }}}
    out = company.statements_from_companyfacts(facts)
    assert out["income_statement"]["periods"] == ["2024-12-31", "2023-12-31"]
    assert out["income_statement"]["rows"][1] == {"item": "Net income", "values": [2.0, None]}
    assert out["balance_sheet"]["rows"][0]["values"] == [50.0, 40.0]
    with pytest.raises(DataUnavailable):
        company.statements_from_companyfacts({"facts": {}})


def test_financials_endpoint_and_edgar_fallback(client, monkeypatch):
    sign_up_and_in(client, "f@example.com")
    stmts = {"income_statement": {"periods": ["2025-03-31"], "rows": [{"item": "Total revenue", "values": [5.0]}]}}
    monkeypatch.setattr(company, "_yf_statements", lambda s: stmts)
    d = client.get("/api/market/NSE/TCS/financials").json()
    assert d["statements"] == stmts and "balance sheet" in " ".join(d["notes"])

    def down(s):
        raise DataUnavailable("Could not download financial statements from Yahoo Finance.")

    monkeypatch.setattr(company, "_yf_statements", down)
    from app.config import settings

    monkeypatch.setattr(settings, "SEC_USER_AGENT", "Test test@example.com")
    monkeypatch.setattr("app.data.fundamentals.get_edgar_facts", lambda t: {"facts": {"us-gaap": {
        "Assets": {"units": {"USD": [{"end": "2024-12-31", "val": 9, "fp": "FY", "form": "10-K", "filed": "2025-02-01"}]}}}}})
    d = client.get("/api/market/NASDAQ/MSFT/financials").json()
    assert d["provenance"]["source"].startswith("SEC EDGAR") and "balance_sheet" in d["statements"]

    monkeypatch.setattr(settings, "SEC_USER_AGENT", "")
    assert client.get("/api/market/NYSE/JPM/financials").status_code == 503


# ---------------- retrieval log ----------------

def test_retrievals_are_logged_once_and_private_to_each_user(client, monkeypatch):
    monkeypatch.setattr(company, "_yf_profile", lambda s: {k: None for k in company.PROFILE_FIELDS})
    sign_up_and_in(client, "l1@example.com")
    for _ in range(3):
        client.get("/api/market/NSE/TCS/prices")
    client.get("/api/market/NSE/TCS/profile")
    log = client.get("/api/market/retrievals").json()
    assert sorted(r["dataset"] for r in log) == ["prices", "profile"]  # three identical views = one entry
    assert {r["ticker"] for r in log} == {"TCS"} and log[0]["source"]

    sign_up_and_in(client, "l2@example.com")
    assert client.get("/api/market/retrievals").json() == []
    with SessionLocal() as db:
        assert db.query(DataRetrieval).count() >= 2
