
from unittest.mock import patch, MagicMock

import pandas as pd


def create_mock_statement():
    return pd.DataFrame(
        {
            pd.Timestamp("2025-12-31"): [1000.0, 400.0],
            pd.Timestamp("2024-12-31"): [800.0, 300.0],
        },
        index=["Total Revenue", "Net Income"]
    )


def create_mock_stock():
    mock_stock = MagicMock()

    statement = create_mock_statement()

    mock_stock.income_stmt = statement
    mock_stock.quarterly_income_stmt = statement
    mock_stock.balance_sheet = statement
    mock_stock.quarterly_balance_sheet = statement
    mock_stock.cashflow = statement
    mock_stock.quarterly_cashflow = statement

    mock_stock.fast_info = {"currency": "INR"}

    return mock_stock


def test_stock_financial_statements_success(client):
    mock_stock = create_mock_stock()

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"] == "TCS"
    assert data["provider_symbol"] == "TCS.NS"
    assert data["market"] == "NSE"
    assert data["currency"] == "INR"

    assert len(data["statements"]) == 6
    assert len(data["available_statements"]) == 6
    assert data["unavailable_statements"] == []

    statement_names = {
        (item["statement_type"], item["frequency"])
        for item in data["statements"]
    }

    assert ("income_statement", "annual") in statement_names
    assert ("income_statement", "quarterly") in statement_names
    assert ("balance_sheet", "annual") in statement_names
    assert ("balance_sheet", "quarterly") in statement_names
    assert ("cash_flow", "annual") in statement_names
    assert ("cash_flow", "quarterly") in statement_names

    income_statement = next(
        item for item in data["statements"]
        if item["statement_type"] == "income_statement"
        and item["frequency"] == "annual"
    )

    assert len(income_statement["periods"]) == 2

    assert (
        income_statement["periods"][0]["values"]["Total Revenue"]
        == 1000.0
    )

    assert data["data_provider"] == "Yahoo Finance"
    assert data["retrieved_at"] is not None

    mock_ticker.assert_called_once_with("TCS.NS")


def test_stock_financial_statements_missing_data_is_reported(client):
    mock_stock = create_mock_stock()

    mock_stock.balance_sheet = pd.DataFrame()
    mock_stock.quarterly_balance_sheet = pd.DataFrame()

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

    assert response.status_code == 200

    data = response.json()

    assert "balance_sheet_annual" in data["unavailable_statements"]
    assert "balance_sheet_quarterly" in data["unavailable_statements"]

    assert "income_statement_annual" in data["available_statements"]
    assert "cash_flow_annual" in data["available_statements"]


def test_stock_financial_statements_unsupported_market_returns_400(client):
    response = client.get(
        "/api/stocks/TCS/financials",
        params={"market": "TOR"}
    )

    assert response.status_code == 400


def test_stock_financial_statements_provider_error_returns_502(client):
    with patch(
        "app.services.market_data.yf.Ticker",
        side_effect=Exception("Provider unavailable")
    ):
        response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

    assert response.status_code == 502


def test_stock_financial_statements_uses_cache(client):
    mock_stock = create_mock_stock()

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ) as mock_ticker:

        first_response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

        second_response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json() == second_response.json()

    mock_ticker.assert_called_once_with("TCS.NS")

def test_stock_financial_statements_all_requests_fail_returns_502(client):
    mock_stock = MagicMock()

    failing_attributes = [
        "income_stmt",
        "quarterly_income_stmt",
        "balance_sheet",
        "quarterly_balance_sheet",
        "cashflow",
        "quarterly_cashflow",
    ]

    for attribute in failing_attributes:
        setattr(
            type(mock_stock),
            attribute,
            property(
                lambda self: (_ for _ in ()).throw(
                    Exception("Statement provider failure")
                )
            )
        )

    mock_stock.fast_info = {"currency": "INR"}

    with patch(
        "app.services.market_data.yf.Ticker",
        return_value=mock_stock
    ):
        response = client.get(
            "/api/stocks/TCS/financials",
            params={"market": "NSE"}
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Financial statements are temporarily unavailable"
    )

