
import pytest

from unittest.mock import patch

from app.services.market_data import MarketDataError


MOCK_PROFILE = {
    "ticker": "TCS.NS",
    "provider_symbol": "TCS.NS",
    "company_name": "Tata Consultancy Services Limited",
    "market": "NSE",
    "exchange": "NSI",
    "sector": "Technology",
    "industry": "Information Technology Services",
    "description": "IT services company",
    "country": "India",
    "currency": "INR",
    "website": "https://www.tcs.com",
    "market_cap": 8609238876160,
    "employees": 584519,
    "data_provider": "Yahoo Finance",
    "retrieved_at": "2026-11-18T20:12:39.309231Z"
}


def test_get_stock_profile_success(client):
    with patch(
        "app.routes.stock_data.get_stock_profile",
        return_value=MOCK_PROFILE
    ) as mock_profile:

        response = client.get(
            "/api/stocks/TCS.NS/profile",
            params={"market": "NSE"}
        )

    assert response.status_code == 200
    assert response.json()["ticker"] == "TCS.NS"
    assert response.json()["market"] == "NSE"
    assert response.json()["currency"] == "INR"
    assert response.json()["company_name"] == (
        "Tata Consultancy Services Limited"
    )

    mock_profile.assert_called_once_with(
        ticker="TCS.NS",
        market="NSE"
    )


def test_stock_profile_unsupported_market_returns_400(client):
    with patch(
        "app.routes.stock_data.get_stock_profile",
        side_effect=ValueError("Unsupported market")
    ):
        response = client.get(
            "/api/stocks/TCS.NS/profile",
            params={"market": "TOR"}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported market"


def test_stock_profile_provider_error_returns_502(client):
    with patch(
        "app.routes.stock_data.get_stock_profile",
        side_effect=MarketDataError(
            "Company profile is temporarily unavailable"
        )
    ):
        response = client.get(
            "/api/stocks/TCS.NS/profile",
            params={"market": "NSE"}
        )

    assert response.status_code == 502


def test_stock_profile_requires_market(client):
    response = client.get(
        "/api/stocks/TCS.NS/profile"
    )

    assert response.status_code == 422

def test_stock_profile_service_uses_cache():
    from app.services.market_data import (
        get_stock_profile,
        clear_market_data_cache
    )

    clear_market_data_cache()

    mock_stock = patch(
        "app.services.market_data.yf.Ticker"
    )

    with mock_stock as mock_ticker:
        mock_ticker.return_value.info = {
            "longName": "Tata Consultancy Services Limited",
            "currency": "INR",
            "exchange": "NSI"
        }

        first_result = get_stock_profile("TCS", "NSE")
        second_result = get_stock_profile("TCS", "NSE")

        assert first_result == second_result
        mock_ticker.assert_called_once_with("TCS.NS")

    clear_market_data_cache()


def test_stock_profile_cache_is_separated_by_market():
    from app.services.market_data import (
        get_stock_profile,
        clear_market_data_cache
    )

    clear_market_data_cache()

    with patch(
        "app.services.market_data.yf.Ticker"
    ) as mock_ticker:

        mock_ticker.return_value.info = {
            "longName": "Example Company",
            "currency": "USD",
            "exchange": "NMS"
        }

        get_stock_profile("ABC", "NASDAQ")
        get_stock_profile("ABC", "NYSE")

        assert mock_ticker.call_count == 2

    clear_market_data_cache()

def test_stock_profile_cache_expires():
    from unittest.mock import patch
    from app.services.market_data import (
        get_stock_profile,
        clear_market_data_cache
    )

    clear_market_data_cache()

    with patch(
        "app.services.market_data.yf.Ticker"
    ) as mock_ticker:

        mock_ticker.return_value.info = {
            "longName": "Example Company",
            "currency": "USD",
            "exchange": "NMS"
        }

        with patch(
            "app.services.market_data.time.monotonic",
            side_effect=[100, 100, 100 + 6 * 60 * 60 + 1, 100 + 6 * 60 * 60 + 1]
        ):
            get_stock_profile("ABC", "NASDAQ")
            get_stock_profile("ABC", "NASDAQ")

        assert mock_ticker.call_count == 2

    clear_market_data_cache()

def test_stock_profile_failure_is_not_cached():
    from app.services.market_data import (
        get_stock_profile,
        clear_market_data_cache,
        MarketDataError
    )

    clear_market_data_cache()

    with patch(
        "app.services.market_data.yf.Ticker"
    ) as mock_ticker:

        mock_ticker.return_value.info = {}

        with pytest.raises(MarketDataError):
            get_stock_profile("ABC", "NASDAQ")

        mock_ticker.return_value.info = {
            "longName": "Example Company",
            "currency": "USD",
            "exchange": "NMS"
        }

        result = get_stock_profile("ABC", "NASDAQ")

        assert result["company_name"] == "Example Company"
        assert mock_ticker.call_count == 2

    clear_market_data_cache()

