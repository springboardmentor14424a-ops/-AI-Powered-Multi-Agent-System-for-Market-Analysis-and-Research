
from unittest.mock import patch

from app.routes.stock_search import get_stock_market


def test_stock_market_mapping():
    assert get_stock_market("TCS.NS", "NSI") == "NSE"
    assert get_stock_market("TCS.BO", "BSE") == "BSE"
    assert get_stock_market("AAPL", "NMS") == "NASDAQ"
    assert get_stock_market("MSFT", "NYQ") == "NYSE"


def test_stock_market_suffix_fallback():
    assert get_stock_market("TCS.NS", "UNKNOWN") == "NSE"
    assert get_stock_market("TCS.BO", "UNKNOWN") == "BSE"


def test_unsupported_market_returns_none():
    assert get_stock_market("TCS.TO", "TOR") is None
    assert get_stock_market("ABC.DE", "GER") is None


def test_stock_search_filters_non_equities(client):
    fake_quotes = [
        {
            "quoteType": "EQUITY",
            "symbol": "TCS.NS",
            "longname": "Tata Consultancy Services Limited",
            "exchange": "NSI"
        },
        {
            "quoteType": "ETF",
            "symbol": "TEST",
            "longname": "Test ETF",
            "exchange": "NMS"
        },
        {
            "quoteType": "EQUITY",
            "symbol": "TCS.TO",
            "shortname": "Tecsys Inc.",
            "exchange": "TOR"
        }
    ]

    class FakeSearch:
        def __init__(self, query, max_results):
            self.quotes = fake_quotes

    with patch(
        "app.routes.stock_search.yf.Search",
        FakeSearch
    ):
        response = client.get(
            "/api/stocks/search",
            params={"query": "TCS"}
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 2

    assert data["results"][0]["ticker"] == "TCS.NS"
    assert data["results"][0]["market"] == "NSE"

    assert data["results"][1]["ticker"] == "TCS.TO"
    assert data["results"][1]["market"] is None


def test_stock_search_provider_error_returns_502(client):
    def failing_search(*args, **kwargs):
        raise Exception("Provider unavailable")

    with patch(
        "app.routes.stock_search.yf.Search",
        side_effect=failing_search
    ):
        response = client.get(
            "/api/stocks/search",
            params={"query": "TCS"}
        )

    assert response.status_code == 502


def test_stock_search_blank_query_returns_400(client):
    response = client.get(
        "/api/stocks/search",
        params={"query": "   "}
    )

    assert response.status_code == 400
