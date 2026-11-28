"""
test_fundamental_agent_service.py
==================================
Unit tests for the Dynamic Fundamental Agent Service
(backend/app/services/fundamental_agent_service.py).

Guarantees:
  - 100% mocked data retrieval (zero network or yfinance calls).
  - Tests multiple tickers and markets (TCS, AAPL, RELIANCE).
  - Tests currency handling (INR vs USD).
  - Tests error cases (invalid ticker, missing statements, exceptions).
  - Tests strict JSON compliance (json.dumps(..., allow_nan=False)).
  - Validates mocked Reliance dataset against known outputs.
"""

import json
from pathlib import Path
import unittest
from unittest.mock import patch
import pandas as pd

try:
    from app.services.fundamental_agent_service import (
        analyze_company_fundamentals,
        sanitize_for_strict_json,
        _dict_statement_to_dataframe,
    )
except ImportError:
    from backend.app.services.fundamental_agent_service import (
        analyze_company_fundamentals,
        sanitize_for_strict_json,
        _dict_statement_to_dataframe,
    )

SERVICE_MOD = analyze_company_fundamentals.__module__


class TestFundamentalAgentService(unittest.TestCase):

    def setUp(self):
        # Prevent any network calls from peer auto-discovery during service tests
        self.discover_patcher = patch(f"{SERVICE_MOD}.discover_peer_candidates", return_value=[])
        self.mock_discover = self.discover_patcher.start()
        self.addCleanup(self.discover_patcher.stop)

        # Sample synthetic Income Statement (serialized format from company_data)
        self.sample_income_data = {
            "2026-03-31": {
                "Total Revenue": 1000000000.0,
                "Gross Profit": 300000000.0,
                "Operating Income": 150000000.0,
                "Net Income": 100000000.0,
                "EBITDA": 200000000.0,
                "Diluted Average Shares": 10000000.0,
            },
            "2025-03-31": {
                "Total Revenue": 900000000.0,
                "Gross Profit": 260000000.0,
                "Operating Income": 130000000.0,
                "Net Income": 85000000.0,
                "EBITDA": 175000000.0,
                "Diluted Average Shares": 10000000.0,
            },
        }

        # Sample synthetic Balance Sheet
        self.sample_bs_data = {
            "2026-03-31": {
                "Total Debt": 200000000.0,
                "Net Debt": 100000000.0,
                "Total Assets": 1500000000.0,
                "Stockholders Equity": 800000000.0,
                "Current Assets": 600000000.0,
                "Current Liabilities": 400000000.0,
                "Cash And Cash Equivalents": 100000000.0,
                "Ordinary Shares Number": 10000000.0,
            },
            "2025-03-31": {
                "Total Debt": 180000000.0,
                "Net Debt": 90000000.0,
                "Total Assets": 1300000000.0,
                "Stockholders Equity": 700000000.0,
                "Current Assets": 500000000.0,
                "Current Liabilities": 350000000.0,
                "Cash And Cash Equivalents": 90000000.0,
                "Ordinary Shares Number": 10000000.0,
            },
        }

    # -----------------------------------------------------------------------
    # 1. Successful Analysis with Multiple Tickers (INR & USD)
    # -----------------------------------------------------------------------
    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_analyze_tcs_inr_success(self, mock_profile, mock_statements):
        mock_profile.return_value = {
            "success": True,
            "profile": {
                "company_name": "Tata Consultancy Services Limited",
                "currency": "INR",
                "sector": "Technology",
                "industry": "Information Technology Services",
                "current_price": 3500.0,
            },
            "data_source": "Yahoo Finance (mock)",
        }

        def _mock_stmt_side_effect(ticker, market, statement, frequency="annual"):
            if statement == "income":
                return {"success": True, "data": self.sample_income_data, "reporting_periods": ["2026-03-31", "2025-03-31"]}
            elif statement == "balance_sheet":
                return {"success": True, "data": self.sample_bs_data, "reporting_periods": ["2026-03-31", "2025-03-31"]}
            return {"success": False, "data": None}

        mock_statements.side_effect = _mock_stmt_side_effect

        result = analyze_company_fundamentals(ticker="TCS", market="NSE")

        self.assertTrue(result["success"])
        self.assertEqual(result["agent_name"], "Fundamental Agent")
        self.assertEqual(result["ticker"], "TCS")
        self.assertEqual(result["market"], "NSE")
        self.assertEqual(result["currency"], "INR")
        self.assertEqual(result["company_name"], "Tata Consultancy Services Limited")
        self.assertEqual(result["market_price"], 3500.0)

        # Check analysis components
        analysis = result["analysis"]
        self.assertIn("revenue_earnings", analysis)
        self.assertIn("profitability", analysis)
        self.assertIn("debt_stability", analysis)
        self.assertIn("financial_ratios", analysis)
        self.assertIn("historical_detail", analysis)
        self.assertIn("data_quality", analysis)
        self.assertIn("profitability_classification", analysis)

        # Verify strict JSON serialization (allow_nan=False MUST succeed)
        json_str = json.dumps(result, allow_nan=False)
        self.assertIsInstance(json_str, str)
        self.assertIn('"agent_name": "Fundamental Agent"', json_str)

    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_analyze_aapl_usd_success(self, mock_profile, mock_statements):
        mock_profile.return_value = {
            "success": True,
            "profile": {
                "company_name": "Apple Inc.",
                "currency": "USD",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "current_price": 225.0,
            },
            "data_source": "Yahoo Finance (mock)",
        }

        mock_statements.side_effect = lambda t, m, statement, frequency="annual": {
            "success": True,
            "data": self.sample_income_data if statement == "income" else self.sample_bs_data,
            "reporting_periods": ["2026-03-31", "2025-03-31"],
        }

        result = analyze_company_fundamentals(ticker="AAPL", market="NASDAQ")

        self.assertTrue(result["success"])
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["market"], "NASDAQ")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["company_name"], "Apple Inc.")

        # Strict JSON serialization check
        json.dumps(result, allow_nan=False)

    # -----------------------------------------------------------------------
    # 2. Error and Missing Data Handling
    # -----------------------------------------------------------------------
    def test_empty_ticker_rejection(self):
        result = analyze_company_fundamentals(ticker="", market="NSE")
        self.assertFalse(result["success"])
        self.assertIn("Ticker symbol must be provided", result["error"])
        json.dumps(result, allow_nan=False)

    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_invalid_ticker_handling(self, mock_profile):
        mock_profile.return_value = {
            "success": False,
            "message": "No company profile found for 'INVALID'.",
            "profile": None,
        }

        result = analyze_company_fundamentals(ticker="INVALID", market="NSE")
        self.assertFalse(result["success"])
        self.assertIn("Company profile retrieval failed", result["error"])
        json.dumps(result, allow_nan=False)

    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_missing_income_statement_failure(self, mock_profile, mock_statements):
        mock_profile.return_value = {
            "success": True,
            "profile": {"company_name": "Test Co", "currency": "INR"},
        }
        mock_statements.return_value = {"success": False, "message": "Income statement unavailable", "data": None}

        result = analyze_company_fundamentals(ticker="NO_INC", market="NSE")
        self.assertFalse(result["success"])
        self.assertIn("Annual income statement could not be retrieved", result["error"])
        json.dumps(result, allow_nan=False)

    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_missing_balance_sheet_graceful(self, mock_profile, mock_statements):
        # Income statement succeeds, but balance sheet fails
        mock_profile.return_value = {
            "success": True,
            "profile": {"company_name": "Asset-Light Co", "currency": "INR", "current_price": 100.0},
        }

        def _side_effect(t, m, statement, frequency="annual"):
            if statement == "income":
                return {"success": True, "data": self.sample_income_data, "reporting_periods": ["2026-03-31"]}
            return {"success": False, "message": "BS missing", "data": None}

        mock_statements.side_effect = _side_effect

        result = analyze_company_fundamentals(ticker="NO_BS", market="NSE")

        # Must succeed gracefully!
        self.assertTrue(result["success"])
        self.assertEqual(result["analysis"]["debt_stability"], [])  # Empty because BS is missing
        # Income-based features still compute
        self.assertTrue(len(result["analysis"]["profitability"]) > 0)
        # Check warning registered
        warnings = [i["Description"] for i in result["analysis"]["data_quality"]["issues"]]
        self.assertTrue(any("Annual balance sheet was unavailable" in w for w in warnings))

        # Strict JSON
        json.dumps(result, allow_nan=False)

    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_missing_market_price_graceful(self, mock_profile, mock_statements):
        # Profile has no market price (e.g. delisted or OTC)
        mock_profile.return_value = {
            "success": True,
            "profile": {"company_name": "Unlisted Co", "currency": "INR", "current_price": None},
        }
        mock_statements.side_effect = lambda t, m, statement="income", frequency="annual": {
            "success": True,
            "data": self.sample_income_data if statement == "income" else self.sample_bs_data,
        }

        result = analyze_company_fundamentals(ticker="NO_PRICE", market="NSE")
        self.assertTrue(result["success"])
        self.assertIsNone(result["market_price"])
        # Valuation multiples in financial ratios remain null
        ratios = result["analysis"]["financial_ratios"]
        self.assertIsNone(ratios[-1]["PE_Ratio"])
        self.assertIsNone(ratios[-1]["PB_Ratio"])

        json.dumps(result, allow_nan=False)

    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_exception_handling(self, mock_profile):
        mock_profile.side_effect = RuntimeError("Network timeout simulation")
        result = analyze_company_fundamentals(ticker="TIMEOUT", market="NSE")
        self.assertFalse(result["success"])
        self.assertIn("Network timeout simulation", result["error"])
        json.dumps(result, allow_nan=False)

    # -----------------------------------------------------------------------
    # 3. Optional Peer Comparison Integration
    # -----------------------------------------------------------------------
    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_optional_peer_comparison(self, mock_profile, mock_statements):
        mock_profile.return_value = {
            "success": True,
            "profile": {"company_name": "Target Co", "currency": "INR", "current_price": 500.0},
        }
        mock_statements.side_effect = lambda t, m, statement="income", frequency="annual": {
            "success": True,
            "data": self.sample_income_data if statement == "income" else self.sample_bs_data,
        }
        self.mock_discover.return_value = []

        # Call without peers and empty discovery -> peer_comparison has unavailable status
        res_no_peers = analyze_company_fundamentals(ticker="TARGET", market="NSE")
        self.assertTrue(res_no_peers["success"])
        self.assertIsNotNone(res_no_peers["analysis"]["peer_comparison"])
        self.assertEqual(res_no_peers["analysis"]["peer_comparison"]["status"], "unavailable")
        self.assertEqual(res_no_peers["analysis"]["peer_comparison"]["peer_count"], 0)

        # Call with explicit peers -> peer_comparison populated
        peers = [
            {"ticker": "PEER1", "currency": "INR", "Net_Profit_Margin_%": 12.0},
            {"ticker": "PEER2", "currency": "INR", "Net_Profit_Margin_%": 8.0},
        ]
        res_with_peers = analyze_company_fundamentals(ticker="TARGET", market="NSE", peer_companies=peers)
        self.assertTrue(res_with_peers["success"])
        self.assertIsNotNone(res_with_peers["analysis"]["peer_comparison"])
        self.assertEqual(res_with_peers["analysis"]["peer_comparison"]["peer_count"], 2)

    # -----------------------------------------------------------------------
    # 4. Mocked Reliance Parity Validation (without live network calls)
    # -----------------------------------------------------------------------
    @patch(f"{SERVICE_MOD}.get_financial_statements")
    @patch(f"{SERVICE_MOD}.get_company_profile")
    def test_mocked_reliance_dataset_parity(self, mock_profile, mock_statements):
        data_dir = Path(__file__).resolve().parents[1] / "ml" / "financial_agent" / "data" / "processed"
        inc_csv = data_dir / "reliance_annual_income_statement.csv"
        bs_csv  = data_dir / "reliance_annual_balance_sheet.csv"

        if not (inc_csv.exists() and bs_csv.exists()):
            self.skipTest("Reliance CSVs not available for mocked test")

        inc_df = pd.read_csv(inc_csv, index_col=0)
        bs_df  = pd.read_csv(bs_csv, index_col=0)

        # Convert to serialized dict shape returned by company_data
        inc_data = {col: inc_df[col].dropna().to_dict() for col in inc_df.columns}
        bs_data  = {col: bs_df[col].dropna().to_dict() for col in bs_df.columns}

        mock_profile.return_value = {
            "success": True,
            "profile": {
                "company_name": "Reliance Industries Limited",
                "currency": "INR",
                "sector": "Energy",
                "industry": "Oil & Gas Refining & Marketing",
                "current_price": 1351.0,
            },
            "data_source": "Yahoo Finance (mocked local fixture)",
        }

        def _side_effect(t, m, statement, frequency="annual"):
            if statement == "income":
                return {"success": True, "data": inc_data, "reporting_periods": list(inc_data.keys())}
            elif statement == "balance_sheet":
                return {"success": True, "data": bs_data, "reporting_periods": list(bs_data.keys())}
            return {"success": False, "data": None}

        mock_statements.side_effect = _side_effect

        result = analyze_company_fundamentals(ticker="RELIANCE.NS", market="NSE")

        self.assertTrue(result["success"])
        self.assertEqual(result["company_name"], "Reliance Industries Limited")
        self.assertEqual(result["currency"], "INR")

        # Verify exact analytical outputs
        analysis = result["analysis"]
        prof_class = analysis["profitability_classification"]["summary"]
        prof_dict = {row["Item"]: row["Value"] for row in prof_class}

        self.assertEqual(prof_dict["Overall Profitability Class"], "Moderately Profitable")
        self.assertEqual(prof_dict["Latest Net Profit Margin (%)"], "7.64%")

        # Strict JSON test with allow_nan=False (raises ValueError if any float NaN/Inf exists)
        json_output = json.dumps(result, allow_nan=False)
        self.assertIsInstance(json_output, str)
        parsed = json.loads(json_output)
        self.assertTrue(parsed["success"])
        self.assertNotIn(": NaN", json_output)


if __name__ == "__main__":
    unittest.main()
