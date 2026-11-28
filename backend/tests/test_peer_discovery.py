"""
test_peer_discovery.py
======================
Unit tests for the Peer Discovery and Automatic Comparison integration
(backend/app/services/peer_discovery.py & fundamental_agent_service.py).

Guarantees:
  - 100% mocked provider calls (zero network/Yahoo Finance requests).
  - Tests Tier 1 (screener), Tier 2 (industry hierarchy), Tier 3 (search fallback).
  - Tests target ticker exclusion and duplicate candidate deduplication.
  - Tests provider failures, empty results, and missing statements.
  - Tests currency mismatch and partial metrics handling.
  - Tests that peer discovery errors NEVER break the target company analysis.
  - Validates strict JSON compliance (json.dumps(..., allow_nan=False)).
"""

import json
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from app.services.peer_discovery import (
    discover_peer_candidates,
    discover_peer_tickers,
    normalize_ticker,
    normalize_industry_key,
    is_same_ticker,
    get_market_region,
)
from app.services.fundamental_agent_service import (
    analyze_company_fundamentals,
    _fetch_peer_metrics,
)


class TestPeerDiscovery(unittest.TestCase):

    def test_normalize_ticker(self):
        self.assertEqual(normalize_ticker("TCS.NS"), "TCS")
        self.assertEqual(normalize_ticker("RELIANCE.BO"), "RELIANCE")
        self.assertEqual(normalize_ticker("AAPL"), "AAPL")
        self.assertEqual(normalize_ticker(" msft "), "MSFT")
        self.assertEqual(normalize_ticker(""), "")

    def test_normalize_industry_key(self):
        self.assertEqual(
            normalize_industry_key("Information Technology Services"),
            "information-technology-services",
        )
        self.assertEqual(
            normalize_industry_key("Oil & Gas Integrated"),
            "oil-gas-integrated",
        )
        self.assertEqual(
            normalize_industry_key("Consumer Electronics"),
            "consumer-electronics",
        )
        self.assertIsNone(normalize_industry_key(None))
        self.assertIsNone(normalize_industry_key(""))

    def test_is_same_ticker(self):
        self.assertTrue(is_same_ticker("TCS.NS", "TCS"))
        self.assertTrue(is_same_ticker("INFY.BO", "INFY.NS"))
        self.assertTrue(is_same_ticker("aapl", "AAPL"))
        self.assertFalse(is_same_ticker("TCS", "INFY"))

    def test_get_market_region(self):
        self.assertEqual(get_market_region("NSE"), "in")
        self.assertEqual(get_market_region("BSE"), "in")
        self.assertEqual(get_market_region("NASDAQ"), "us")
        self.assertEqual(get_market_region("NYSE"), "us")

    @patch("app.services.peer_discovery.yf")
    def test_tier1_screener_success(self, mock_yf):
        # Setup mock EquityQuery and screen
        mock_yf.EquityQuery = MagicMock()
        mock_yf.screen.return_value = {
            "quotes": [
                {"symbol": "TCS.NS", "shortName": "Tata Consultancy", "marketCap": 15000000000000},
                {"symbol": "INFY.NS", "shortName": "Infosys Ltd", "marketCap": 8000000000000},
                {"symbol": "WIPRO.NS", "shortName": "Wipro Ltd", "marketCap": 3000000000000},
                {"symbol": "HCLTECH.NS", "shortName": "HCL Tech", "marketCap": 4500000000000},
                {"symbol": "TECHM.NS", "shortName": "Tech Mahindra", "marketCap": 1600000000000},
            ]
        }

        candidates = discover_peer_candidates(
            target_ticker="TCS",
            market="NSE",
            sector="Technology",
            industry="Information Technology Services",
            max_peers=4,
        )

        # TCS must be excluded
        candidate_syms = [c["clean_ticker"] for c in candidates]
        self.assertNotIn("TCS", candidate_syms)
        # Should have top peers sorted by market cap
        self.assertIn("INFY", candidate_syms)
        self.assertIn("HCLTECH", candidate_syms)
        self.assertIn("WIPRO", candidate_syms)
        self.assertLessEqual(len(candidates), 4)

    @patch("app.services.peer_discovery.yf")
    def test_tier2_industry_hierarchy_fallback(self, mock_yf):
        # Tier 1 fails or returns empty
        mock_yf.EquityQuery = MagicMock()
        mock_yf.screen.return_value = {"quotes": []}

        # Mock yf.Industry
        mock_industry = MagicMock()
        df_top = pd.DataFrame(
            [
                {"name": "Infosys", "market_cap": 8000000000},
                {"name": "Wipro", "market_cap": 3000000000},
            ],
            index=["INFY.NS", "WIPRO.NS"],
        )
        mock_industry.top_companies = df_top
        mock_yf.Industry.return_value = mock_industry

        candidates = discover_peer_candidates(
            target_ticker="TCS",
            market="NSE",
            industry_key="information-technology-services",
            max_peers=3,
        )

        syms = [c["clean_ticker"] for c in candidates]
        self.assertIn("INFY", syms)
        self.assertIn("WIPRO", syms)
        self.assertNotIn("TCS", syms)

    @patch("app.services.peer_discovery.yf")
    def test_tier3_search_fallback(self, mock_yf):
        # Tier 1 and Tier 2 return empty
        mock_yf.screen.return_value = {"quotes": []}
        mock_yf.Industry.return_value.top_companies = None

        # Tier 3 search returns quotes
        mock_search = MagicMock()
        mock_search.quotes = [
            {"symbol": "MSFT", "quoteType": "EQUITY", "shortname": "Microsoft Corp"},
            {"symbol": "GOOGL", "quoteType": "EQUITY", "shortname": "Alphabet Inc"},
            {"symbol": "AAPL", "quoteType": "EQUITY", "shortname": "Apple Inc"},
        ]
        mock_yf.Search.return_value = mock_search

        candidates = discover_peer_candidates(
            target_ticker="AAPL",
            market="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            max_peers=3,
        )

        syms = [c["clean_ticker"] for c in candidates]
        self.assertNotIn("AAPL", syms)
        self.assertIn("MSFT", syms)
        self.assertIn("GOOGL", syms)

    @patch("app.services.peer_discovery.yf")
    def test_target_exclusion_and_deduplication(self, mock_yf):
        # Test that duplicate symbols (even with different suffixes) are deduplicated
        mock_yf.screen.return_value = {
            "quotes": [
                {"symbol": "TCS.NS", "marketCap": 100},
                {"symbol": "TCS.BO", "marketCap": 100},
                {"symbol": "INFY.NS", "marketCap": 50},
                {"symbol": "INFY.BO", "marketCap": 50},
            ]
        }

        tickers = discover_peer_tickers(
            target_ticker="TCS",
            market="NSE",
            sector="Technology",
        )

        # Only INFY should remain, exactly once
        self.assertEqual(tickers, ["INFY"])

    @patch("app.services.peer_discovery.yf")
    def test_graceful_handling_of_discovery_exceptions(self, mock_yf):
        # If yf.screen throws network error
        mock_yf.screen.side_effect = ConnectionError("Network unreachable")
        mock_yf.Industry.side_effect = RuntimeError("Service down")
        mock_yf.Search.side_effect = Exception("API error")

        candidates = discover_peer_candidates(
            target_ticker="RELIANCE",
            market="NSE",
            sector="Energy",
        )
        self.assertEqual(candidates, [])


class TestPeerIntegrationInService(unittest.TestCase):

    def setUp(self):
        self.sample_income = {
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
        self.sample_bs = {
            "2026-03-31": {
                "Total Assets": 1200000000.0,
                "Current Assets": 600000000.0,
                "Current Liabilities": 300000000.0,
                "Total Debt": 200000000.0,
                "Stockholders Equity": 700000000.0,
            },
            "2025-03-31": {
                "Total Assets": 1050000000.0,
                "Current Assets": 500000000.0,
                "Current Liabilities": 250000000.0,
                "Total Debt": 180000000.0,
                "Stockholders Equity": 620000000.0,
            },
        }

    @patch("app.services.fundamental_agent_service.discover_peer_candidates")
    @patch("app.services.fundamental_agent_service.get_financial_statements")
    @patch("app.services.fundamental_agent_service.get_company_profile")
    def test_auto_peer_discovery_and_comparison_success(
        self, mock_profile, mock_statements, mock_discover
    ):
        # Mock discovery returning two peers
        mock_discover.return_value = [
            {"clean_ticker": "INFY", "symbol": "INFY.NS", "market_cap": 8000000000},
            {"clean_ticker": "WIPRO", "symbol": "WIPRO.NS", "market_cap": 3000000000},
        ]

        def profile_side_effect(tick, mkt):
            clean = normalize_ticker(tick)
            if clean == "TCS":
                return {
                    "success": True,
                    "profile": {
                        "company_name": "Tata Consultancy",
                        "currency": "INR",
                        "sector": "Technology",
                        "industry": "IT Services",
                        "current_price": 3800.0,
                    },
                }
            elif clean == "INFY":
                return {
                    "success": True,
                    "profile": {
                        "company_name": "Infosys Limited",
                        "currency": "INR",
                        "sector": "Technology",
                        "industry": "IT Services",
                        "current_price": 1600.0,
                    },
                }
            elif clean == "WIPRO":
                return {
                    "success": True,
                    "profile": {
                        "company_name": "Wipro Limited",
                        "currency": "INR",
                        "sector": "Technology",
                        "industry": "IT Services",
                        "current_price": 500.0,
                    },
                }
            return {"success": False}

        mock_profile.side_effect = profile_side_effect
        mock_statements.side_effect = lambda t, m, statement="income", frequency="annual": {
            "success": True,
            "data": self.sample_income if statement == "income" else self.sample_bs,
        }

        # Analyze without supplying peer_companies
        result = analyze_company_fundamentals(ticker="TCS", market="NSE")

        self.assertTrue(result["success"])
        analysis = result["analysis"]
        self.assertIn("peer_comparison", analysis)
        peer_comp = analysis["peer_comparison"]

        self.assertIsNotNone(peer_comp)
        self.assertEqual(peer_comp.get("discovery_status"), "auto_discovered")
        self.assertEqual(peer_comp["target_ticker"], "TCS")
        self.assertEqual(peer_comp["peer_count"], 2)
        self.assertEqual(peer_comp["companies_compared"], 3)  # Target + 2 peers

        # Validate benchmarks exist
        benchmarks = peer_comp.get("peer_benchmarks", {})
        self.assertIn("Net_Profit_Margin_%", benchmarks)
        npm_bench = benchmarks["Net_Profit_Margin_%"]
        self.assertIsNotNone(npm_bench.get("peer_average"))
        self.assertEqual(npm_bench.get("peer_count"), 2)

        # Validate strict JSON serialization
        json_str = json.dumps(result, allow_nan=False)
        self.assertTrue(len(json_str) > 0)

    @patch("app.services.fundamental_agent_service.discover_peer_candidates")
    @patch("app.services.fundamental_agent_service.get_financial_statements")
    @patch("app.services.fundamental_agent_service.get_company_profile")
    def test_peer_failure_does_not_break_target_analysis(
        self, mock_profile, mock_statements, mock_discover
    ):
        # Target succeeds, but peer discovery raises an exception
        mock_discover.side_effect = Exception("Discovery API totally offline")

        mock_profile.return_value = {
            "success": True,
            "profile": {
                "company_name": "Tata Consultancy",
                "currency": "INR",
                "sector": "Technology",
                "current_price": 3800.0,
            },
        }
        mock_statements.side_effect = lambda t, m, statement="income", frequency="annual": {
            "success": True,
            "data": self.sample_income if statement == "income" else self.sample_bs,
        }

        result = analyze_company_fundamentals(ticker="TCS", market="NSE")

        # Main analysis MUST succeed
        self.assertTrue(result["success"])
        self.assertEqual(result["ticker"], "TCS")
        self.assertIn("revenue_earnings", result["analysis"])
        self.assertIn("profitability", result["analysis"])
        self.assertIn("profitability_classification", result["analysis"])

        # Feature 6 should return graceful unavailable status
        peer_comp = result["analysis"]["peer_comparison"]
        self.assertEqual(peer_comp["status"], "unavailable")
        self.assertEqual(peer_comp["peer_count"], 0)
        self.assertTrue(any("Automatic peer discovery" in w for w in peer_comp.get("warnings", [])))

        # Strict JSON compliance holds
        json_str = json.dumps(result, allow_nan=False)
        self.assertTrue(len(json_str) > 0)

    @patch("app.services.fundamental_agent_service.get_financial_statements")
    @patch("app.services.fundamental_agent_service.get_company_profile")
    def test_fetch_peer_metrics_handles_missing_data(self, mock_profile, mock_statements):
        # 1. Profile fails
        mock_profile.return_value = {"success": False}
        self.assertIsNone(_fetch_peer_metrics("BADPEER", "NSE", "INR"))

        # 2. Profile ok, but income statement missing
        mock_profile.return_value = {"success": True, "profile": {"currency": "INR"}}
        mock_statements.return_value = {"success": False, "data": None}
        self.assertIsNone(_fetch_peer_metrics("BADPEER2", "NSE", "INR"))

    @patch("app.services.fundamental_agent_service.discover_peer_candidates")
    @patch("app.services.fundamental_agent_service.get_financial_statements")
    @patch("app.services.fundamental_agent_service.get_company_profile")
    def test_partial_metrics_and_currency_mismatch(
        self, mock_profile, mock_statements, mock_discover
    ):
        # Target in INR, Peer in USD (Cross-currency)
        mock_discover.return_value = [
            {"clean_ticker": "GLOBE_TECH", "symbol": "GLOBE", "market_cap": 5000000},
        ]

        def profile_side_effect(tick, mkt):
            clean = normalize_ticker(tick)
            if clean == "TCS":
                return {
                    "success": True,
                    "profile": {
                        "company_name": "Tata Consultancy",
                        "currency": "INR",
                        "sector": "Technology",
                        "current_price": 3800.0,
                    },
                }
            return {
                "success": True,
                "profile": {
                    "company_name": "Global Tech Corp",
                    "currency": "USD",
                    "sector": "Technology",
                    "current_price": 120.0,
                },
            }

        mock_profile.side_effect = profile_side_effect

        # Peer has income statement, but balance sheet is missing (partial metrics)
        def stmt_side_effect(tick, mkt, statement="income", frequency="annual"):
            clean = normalize_ticker(tick)
            if clean == "TCS":
                return {
                    "success": True,
                    "data": self.sample_income if statement == "income" else self.sample_bs,
                }
            else:
                if statement == "income":
                    return {"success": True, "data": self.sample_income}
                return {"success": False, "data": None}  # Missing balance sheet for peer

        mock_statements.side_effect = stmt_side_effect

        result = analyze_company_fundamentals(ticker="TCS", market="NSE")
        self.assertTrue(result["success"])

        peer_comp = result["analysis"]["peer_comparison"]
        self.assertEqual(peer_comp["peer_count"], 1)

        # Check currency mismatch warning
        warnings = peer_comp.get("warnings", [])
        self.assertTrue(any("Currency Mismatch" in w for w in warnings))

        # Monetary benchmark (Revenue_Cr) excludes USD peer
        benchmarks = peer_comp["peer_benchmarks"]
        rev_bench = benchmarks.get("Revenue_Cr", {})
        self.assertEqual(rev_bench.get("peer_count"), 0)  # Excluded due to currency mismatch

        # Percentage benchmark (Net_Profit_Margin_%) includes USD peer
        npm_bench = benchmarks.get("Net_Profit_Margin_%", {})
        self.assertEqual(npm_bench.get("peer_count"), 1)
        self.assertIsNotNone(npm_bench.get("peer_average"))

        # Missing balance sheet for peer means Debt_to_Equity benchmark has 0 valid peer values
        debt_bench = benchmarks.get("Debt_to_Equity", {})
        self.assertEqual(debt_bench.get("peer_count"), 0)

        # Strict JSON compliance holds
        json_str = json.dumps(result, allow_nan=False)
        self.assertTrue(len(json_str) > 0)


if __name__ == "__main__":
    unittest.main()
