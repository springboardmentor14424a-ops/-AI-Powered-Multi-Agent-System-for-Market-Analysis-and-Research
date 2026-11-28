
import pandas as pd
from unittest.mock import patch

from app.services.fundamental_analysis_service import (
    run_fundamental_analysis
)


def test_fundamental_analysis():

    # Sample income statement
    income_statement = pd.DataFrame(
        {
            "2025": [1000000, 200000],
            "2024": [800000, 160000],
        },
        index=[
            "Total Revenue",
            "Net Income"
        ]
    )

    # Sample balance sheet
    balance_sheet = pd.DataFrame(
        {
            "2025": [300000, 500000],
        },
        index=[
            "Total Debt",
            "Stockholders Equity"
        ]
    )

    # Mock external Yahoo Finance data
    with patch(
        "app.services.fundamental_analysis_service.get_financial_statements"
    ) as mock_statements, patch(
        "app.services.fundamental_analysis_service.get_company_profile"
    ) as mock_profile, patch(
        "app.services.fundamental_analysis_service.calculate_valuation_ratios"
    ) as mock_valuation:

        mock_statements.return_value = {
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": pd.DataFrame()
        }

        mock_profile.return_value = {
            "longName": "Test Company",
            "sector": "Technology",
            "industry": "Software"
        }

        mock_valuation.return_value = {
            "pe_ratio": 25.0,
            "pb_ratio": 4.0
        }

        result = run_fundamental_analysis("INFY")

    # Verify company details
    assert result["symbol"] == "INFY"
    assert result["company_name"] == "Test Company"

    # Verify revenue growth
    assert result["revenue_earnings"]["revenue_growth_percent"] == 25.0

    # Verify earnings growth
    assert result["revenue_earnings"]["earnings_growth_percent"] == 25.0

    # Verify profit margin
    assert result["profitability"]["profit_margin_percent"] == 20.0

    # Verify ROE
    assert result["profitability"]["return_on_equity_percent"] == 40.0

    # Verify debt-to-equity
    assert result["financial_stability"]["debt_to_equity_percent"] == 60.0

    # Verify valuation ratios
    assert result["valuation"]["pe_ratio"] == 25.0
    assert result["valuation"]["pb_ratio"] == 4.0

    # Verify metadata
    assert result["metadata"]["source"] == "Yahoo Finance"

    print("PASS: Company details")
    print("PASS: Revenue growth")
    print("PASS: Earnings growth")
    print("PASS: Profit margin")
    print("PASS: Return on Equity")
    print("PASS: Debt-to-equity")
    print("PASS: P/E and P/B ratios")
    print("PASS: Data source metadata")

    print("\nAll Fundamental Analysis tests passed!")


if __name__ == "__main__":
    test_fundamental_analysis()
