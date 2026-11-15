import pytest

from app import yahoo_search
from app.config import settings
from tests.conftest import login, register

FAKE_QUOTES = [
    {"symbol": "TCS.NS", "longname": "Tata Consultancy Services Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "TCS.BO", "shortname": "TCS", "exchange": "BSE", "quoteType": "EQUITY"},
    {"symbol": "ZOMATO.NS", "longname": "Zomato Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "AAPL", "longname": "Apple Inc.", "exchange": "NMS", "quoteType": "EQUITY"},
    {"symbol": "KO", "longname": "The Coca-Cola Company", "exchange": "NYQ", "quoteType": "EQUITY"},
    {"symbol": "SPY", "shortname": "SPDR S&P 500", "exchange": "PCX", "quoteType": "ETF"},  # skipped (ETF)
    {"symbol": "VOD.L", "shortname": "Vodafone", "exchange": "LSE", "quoteType": "EQUITY"},  # skipped (London)
]


@pytest.fixture()
def yahoo_on(monkeypatch):
    monkeypatch.setattr(settings, "YAHOO_SEARCH_ENABLED", True)
    monkeypatch.setattr(yahoo_search, "_raw_quotes", lambda q: FAKE_QUOTES)
    yahoo_search.clear_cache()
    yield
    yahoo_search.clear_cache()


def test_search_uses_yahoo_and_filters_by_market(client, alice, yahoo_on):
    nse = client.get("/api/stocks/search", params={"q": "tcs", "market": "NSE"}).json()
    assert {s["ticker"] for s in nse} == {"TCS", "ZOMATO"}
    assert all(s["source"] == "yahoo" and s["market"] == "NSE" for s in nse)
    us = client.get("/api/stocks/search", params={"q": "apple", "market": "NASDAQ"}).json()
    assert [s["provider_symbol"] for s in us] == ["AAPL"]
    nyse = client.get("/api/stocks/search", params={"q": "coca", "market": "NYSE"}).json()
    assert [s["ticker"] for s in nyse] == ["KO"]  # ETF (SPY) and London listing (VOD.L) are excluded


def test_stock_outside_builtin_list_can_be_saved_and_researched(client, alice, yahoo_on):
    r = client.post("/api/watchlist", json={"ticker": "zomato", "market": "NSE"}, headers=alice)
    assert r.status_code == 201
    assert r.json()["company_name"] == "Zomato Limited"
    t = client.post("/api/research", json={"ticker": "ZOMATO", "market": "NSE"}, headers=alice)
    assert t.status_code == 201


def test_falls_back_to_builtin_list_when_yahoo_fails(client, alice, monkeypatch):
    monkeypatch.setattr(settings, "YAHOO_SEARCH_ENABLED", True)

    def boom(_q):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(yahoo_search, "_raw_quotes", boom)
    yahoo_search.clear_cache()
    r = client.get("/api/stocks/search", params={"q": "tcs", "market": "NSE"}).json()
    assert r and r[0]["ticker"] == "TCS" and r[0]["source"] == "catalog"


def test_unknown_ticker_still_rejected(client, alice, yahoo_on):
    r = client.post("/api/watchlist", json={"ticker": "NOPE", "market": "NSE"}, headers=alice)
    assert r.status_code == 404
