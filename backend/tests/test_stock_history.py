
from unittest.mock import patch, MagicMock

import pandas as pd

from app.services.market_data import MarketDataError


def create_mock_history():
    return pd.DataFrame(
        {
            "Open": [100.0, 105.0, 110.0],
            "High": [110.0, 115.0, 120.0],
            "Low": [95.0, 100.0, 105.0],
            "Close": [105.0, 110.0, 115.0],
            "Adj Close": [105.0, 110.0, 115.0],
            "Volume": [1000, 1500, 2000],
        },
        index=pd.to_datetime(
            [
                "2026-11-16",
                "2026-11-17",
                "2026-11-18",
            ]
        )
    )


def call_history_endpoint(history):
    mock_stock = MagicMock()
    mock_stock.history.return_value = history
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as test_client:
            return test_client.get(
                "/api/stocks/TCS/history",
                params={"market": "NSE", "period": "1M"}
            )


def test_stock_history_success(client):
    mock_stock = MagicMock()
    mock_stock.history.return_value = create_mock_history()
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"] == "TCS"
    assert data["provider_symbol"] == "TCS.NS"
    assert data["market"] == "NSE"
    assert data["period"] == "1M"
    assert data["interval"] == "1d"
    assert data["currency"] == "INR"

    assert data["record_count"] == 3
    assert len(data["records"]) == 3

    assert data["records"][0]["open"] == 100.0
    assert data["records"][0]["close"] == 105.0
    assert data["records"][0]["volume"] == 1000

    assert data["validation"]["is_valid"] is True
    assert data["validation"]["valid_rows"] == 3
    assert data["validation"]["invalid_rows"] == 0
    assert data["validation"]["missing_values"] == 0
    assert data["validation"]["adjusted_close_missing"] == 0
    assert data["validation"]["invalid_timestamps"] == 0
    assert data["validation"]["duplicate_rows"] == 0

    assert data["data_provider"] == "Yahoo Finance"

    mock_ticker.assert_called_once_with("TCS.NS")

    mock_stock.history.assert_called_once_with(
        period="1mo",
        interval="1d",
        auto_adjust=False,
        actions=False
    )


def test_stock_history_unsupported_market_returns_400(client):
    response = client.get(
        "/api/stocks/TCS/history",
        params={"market": "TOR", "period": "1M"}
    )

    assert response.status_code == 400


def test_stock_history_unsupported_period_returns_400(client):
    response = client.get(
        "/api/stocks/TCS/history",
        params={"market": "NSE", "period": "10Y"}
    )

    assert response.status_code == 400


def test_stock_history_provider_error_returns_502(client):
    mock_stock = MagicMock()
    mock_stock.history.side_effect = Exception(
        "Provider unavailable"
    )

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 502


def test_stock_history_empty_data_returns_502(client):
    mock_stock = MagicMock()
    mock_stock.history.return_value = pd.DataFrame()

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 502


def test_stock_history_requires_market_and_period(client):
    response = client.get("/api/stocks/TCS/history")

    assert response.status_code == 422


def test_stock_history_missing_adjusted_close_is_reported(client):
    history = create_mock_history()
    history.loc[history.index[0], "Adj Close"] = float("nan")

    response = call_history_endpoint(history)

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 3
    assert data["validation"]["valid_rows"] == 3
    assert data["validation"]["adjusted_close_missing"] == 1
    assert data["validation"]["invalid_rows"] == 0
    assert data["records"][0]["adjusted_close"] is None


def test_stock_history_invalid_ohlc_row_is_rejected(client):
    history = create_mock_history()

    # High price cannot be lower than the opening price.
    history.loc[history.index[0], "High"] = 90.0

    mock_stock = MagicMock()
    mock_stock.history.return_value = history
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 2
    assert data["validation"]["valid_rows"] == 2
    assert data["validation"]["invalid_rows"] == 1
    assert data["validation"]["is_valid"] is False


def test_stock_history_fractional_volume_is_rejected(client):
    history = create_mock_history()
    history["Volume"] = history["Volume"].astype(float)
    history.loc[history.index[0], "Volume"] = 1000.5

    mock_stock = MagicMock()
    mock_stock.history.return_value = history
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 2
    assert data["validation"]["invalid_rows"] == 1
    assert data["validation"]["is_valid"] is False


def test_stock_history_duplicate_timestamps_are_reported(client):
    history = create_mock_history()

    duplicate_row = history.iloc[[0]]
    history = pd.concat([history, duplicate_row])

    mock_stock = MagicMock()
    mock_stock.history.return_value = history
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 3
    assert data["validation"]["valid_rows"] == 3
    assert data["validation"]["duplicate_rows"] == 1
    assert data["validation"]["is_valid"] is False

def test_stock_history_service_uses_cache():
    from app.services.market_data import (
        get_stock_history,
        clear_market_data_cache
    )

    clear_market_data_cache()

    mock_stock = MagicMock()
    mock_stock.history.return_value = create_mock_history()
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        first_result = get_stock_history("TCS", "NSE", "1M")
        second_result = get_stock_history("TCS", "NSE", "1M")

        assert first_result == second_result
        mock_ticker.assert_called_once_with("TCS.NS")
        mock_stock.history.assert_called_once()

    clear_market_data_cache()


def test_stock_history_cache_is_separated_by_period():
    from app.services.market_data import (
        get_stock_history,
        clear_market_data_cache
    )

    clear_market_data_cache()

    mock_stock = MagicMock()
    mock_stock.history.return_value = create_mock_history()
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        get_stock_history("TCS", "NSE", "1M")
        get_stock_history("TCS", "NSE", "3M")

        assert mock_ticker.call_count == 2
        assert mock_stock.history.call_count == 2

    clear_market_data_cache()

def test_stock_history_cache_expires():
    from app.services.market_data import (
        get_stock_history,
        clear_market_data_cache
    )

    clear_market_data_cache()

    mock_stock = MagicMock()
    mock_stock.history.return_value = create_mock_history()
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        with patch(
            "app.services.market_data.time.monotonic",
            side_effect=[
                100,
                100,
                100 + 15 * 60 + 1,
                100 + 15 * 60 + 1
            ]
        ):
            get_stock_history("TCS", "NSE", "1M")
            get_stock_history("TCS", "NSE", "1M")

        assert mock_ticker.call_count == 2
        assert mock_stock.history.call_count == 2

    clear_market_data_cache()


def test_stock_history_invalid_nat_timestamp_is_rejected():
    history = create_mock_history()

    history.index = pd.DatetimeIndex([
        pd.Timestamp("2026-11-16"),
        pd.NaT,
        pd.Timestamp("2026-11-18")
    ])

    response = call_history_endpoint(history)

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 2
    assert data["validation"]["valid_rows"] == 2
    assert data["validation"]["invalid_rows"] == 1
    assert data["validation"]["invalid_timestamps"] == 1
    assert data["validation"]["is_valid"] is False

def test_stock_history_missing_required_values_are_rejected(client):
    history = create_mock_history()

    history.loc[history.index[0], "Close"] = float("nan")
    history.loc[history.index[1], "Volume"] = float("nan")

    mock_stock = MagicMock()
    mock_stock.history.return_value = history
    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/history",
            params={"market": "NSE", "period": "1M"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["record_count"] == 1
    assert data["validation"]["valid_rows"] == 1
    assert data["validation"]["invalid_rows"] == 2
    assert data["validation"]["missing_values"] == 2
    assert data["validation"]["is_valid"] is False

