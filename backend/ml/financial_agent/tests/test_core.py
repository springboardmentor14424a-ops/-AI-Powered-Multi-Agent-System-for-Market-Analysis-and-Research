"""
test_core.py
------------
Unit and integration tests for the in-memory Financial Analysis Engine
(backend/ml/financial_agent/core.py).

Features tested:
  1. Revenue & Earnings Analysis
  2. Profitability Analysis
  3. Debt & Financial Stability Analysis
  4. Financial Ratios Analysis
  5. Historical Performance Comparison
  6. Master Runner (run_fundamental_analysis)
  7. Parity Validation against existing Reliance processed outputs
"""

import json
import math
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

try:
    from ml.financial_agent.core import (
        analyze_revenue_earnings,
        analyze_profitability,
        analyze_debt_stability,
        analyze_financial_ratios,
        compare_historical_performance,
        audit_financial_data_quality,
        classify_profitability_margin,
        classify_profitability,
        compare_peers,
        run_fundamental_analysis,
    )
except ImportError:
    from backend.ml.financial_agent.core import (
        analyze_revenue_earnings,
        analyze_profitability,
        analyze_debt_stability,
        analyze_financial_ratios,
        compare_historical_performance,
        audit_financial_data_quality,
        classify_profitability_margin,
        classify_profitability,
        compare_peers,
        run_fundamental_analysis,
    )


class TestCoreEngineSynthetic(unittest.TestCase):
    """Synthetic unit tests ensuring in-memory execution and edge-case safety."""

    def setUp(self):
        # Synthetic Income Statement (yfinance layout: rows = metrics, cols = dates)
        self.synthetic_inc = pd.DataFrame(
            {
                "2024-03-31": [1000.0, 250.0, 150.0, 100.0, 180.0, 10.0],
                "2025-03-31": [1200.0, 320.0, 200.0, 140.0, 240.0, 10.0],
                "2026-03-31": [1500.0, 420.0, 270.0, 210.0, 310.0, 10.0],
            },
            index=[
                "Total Revenue",
                "Gross Profit",
                "Operating Income",
                "Net Income",
                "EBITDA",
                "Diluted Average Shares",
            ],
        )

        # Synthetic Balance Sheet
        self.synthetic_bs = pd.DataFrame(
            {
                "2024-03-31": [400.0, 250.0, 2000.0, 1000.0, 600.0, 500.0, 150.0, 10.0],
                "2025-03-31": [450.0, 270.0, 2300.0, 1150.0, 700.0, 550.0, 180.0, 10.0],
                "2026-03-31": [500.0, 300.0, 2700.0, 1350.0, 850.0, 600.0, 200.0, 10.0],
            },
            index=[
                "Total Debt",
                "Net Debt",
                "Total Assets",
                "Stockholders Equity",
                "Current Assets",
                "Current Liabilities",
                "Cash And Cash Equivalents",
                "Ordinary Shares Number",
            ],
        )

    # -----------------------------------------------------------------------
    # Feature 1: Revenue & Earnings
    # -----------------------------------------------------------------------
    def test_analyze_revenue_earnings(self):
        res = analyze_revenue_earnings(self.synthetic_inc)
        self.assertEqual(len(res), 3)
        self.assertEqual(res["Financial_Year"].tolist(), ["2024-03-31", "2025-03-31", "2026-03-31"])

        # Base year growth is NaN
        self.assertTrue(pd.isna(res.loc[0, "Revenue_Growth_%"]))

        # Year 2: (1200 - 1000) / 1000 * 100 = +20%
        self.assertAlmostEqual(res.loc[1, "Revenue_Growth_%"], 20.0, places=2)
        # Year 2 earnings: (140 - 100) / 100 * 100 = +40%
        self.assertAlmostEqual(res.loc[1, "Earnings_Growth_%"], 40.0, places=2)
        # Year 2 diffs
        self.assertAlmostEqual(res.loc[1, "Revenue_Trend"], 200.0, places=2)
        self.assertAlmostEqual(res.loc[1, "Earnings_Trend"], 40.0, places=2)

    # -----------------------------------------------------------------------
    # Feature 2: Profitability
    # -----------------------------------------------------------------------
    def test_analyze_profitability(self):
        res = analyze_profitability(self.synthetic_inc)
        self.assertEqual(len(res), 3)

        # 2024: Gross Margin = 250/1000 = 25.0%, Operating = 150/1000 = 15.0%, Net = 100/1000 = 10.0%
        self.assertAlmostEqual(res.loc[0, "Gross_Profit_Margin_%"], 25.0, places=2)
        self.assertAlmostEqual(res.loc[0, "Operating_Margin_%"], 15.0, places=2)
        self.assertAlmostEqual(res.loc[0, "Net_Profit_Margin_%"], 10.0, places=2)
        self.assertAlmostEqual(res.loc[0, "EBITDA_Margin_%"], 18.0, places=2)

        # 2025: Net Margin = 140/1200 = 11.6667% (Improving)
        self.assertAlmostEqual(res.loc[1, "Net_Profit_Margin_%"], 11.6667, places=3)
        self.assertEqual(res.loc[1, "Net_Margin_Status"], "Improving")

    # -----------------------------------------------------------------------
    # Feature 3: Debt Stability
    # -----------------------------------------------------------------------
    def test_analyze_debt_stability(self):
        res = analyze_debt_stability(self.synthetic_bs)
        self.assertEqual(len(res), 3)

        # 2024: Debt to Equity = 400 / 1000 = 0.40
        self.assertAlmostEqual(res.loc[0, "Debt_to_Equity_Ratio"], 0.40, places=4)
        # Debt to Assets = 400 / 2000 = 0.20
        self.assertAlmostEqual(res.loc[0, "Debt_to_Assets_Ratio"], 0.20, places=4)
        # Current Ratio = 600 / 500 = 1.20
        self.assertAlmostEqual(res.loc[0, "Current_Ratio"], 1.20, places=4)
        # Cash to Debt = 150 / 400 = 0.375
        self.assertAlmostEqual(res.loc[0, "Cash_to_Debt_Ratio"], 0.375, places=4)
        # Net Debt to Assets = 250 / 2000 = 0.125
        self.assertAlmostEqual(res.loc[0, "Net_Debt_to_Assets_Ratio"], 0.125, places=4)

    def test_analyze_debt_stability_zero_division(self):
        # Zero equity and zero liabilities
        zero_bs = pd.DataFrame(
            {"2026-03-31": [100.0, 100.0, 500.0, 0.0, 100.0, 0.0, 50.0]},
            index=["Total Debt", "Net Debt", "Total Assets", "Stockholders Equity",
                   "Current Assets", "Current Liabilities", "Cash And Cash Equivalents"]
        )
        res = analyze_debt_stability(zero_bs)
        # Must return None/NaN, not crash
        self.assertTrue(pd.isna(res.loc[0, "Debt_to_Equity_Ratio"]))
        self.assertTrue(pd.isna(res.loc[0, "Current_Ratio"]))

    # -----------------------------------------------------------------------
    # Feature 4: Financial Ratios
    # -----------------------------------------------------------------------
    def test_analyze_financial_ratios(self):
        # Net Income = 210, Equity = 1350, Shares = 10, Price = 50.0
        res = analyze_financial_ratios(self.synthetic_inc, self.synthetic_bs, market_price=50.0, price_date="2026-03-31")
        self.assertEqual(len(res), 3)

        # 2026: ROE = 210 / 1350 * 100 = 15.5556%
        self.assertAlmostEqual(res.loc[2, "ROE_%"], 15.5556, places=3)
        # EPS = 210 / 10 = 21.0
        self.assertAlmostEqual(res.loc[2, "EPS"], 21.0, places=2)
        # BVPS = 1350 / 10 = 135.0
        self.assertAlmostEqual(res.loc[2, "Book_Value_Per_Share"], 135.0, places=2)

        # Valuation multiples must be populated on latest year only
        self.assertTrue(pd.isna(res.loc[0, "PE_Ratio"]))
        self.assertTrue(pd.isna(res.loc[1, "PE_Ratio"]))
        # Latest P/E = 50 / 21 = 2.3810
        self.assertAlmostEqual(res.loc[2, "PE_Ratio"], 2.3810, places=3)
        # Latest P/B = 50 / 135 = 0.3704
        self.assertAlmostEqual(res.loc[2, "PB_Ratio"], 0.3704, places=3)

    # -----------------------------------------------------------------------
    # Feature 5: Historical Performance Comparison
    # -----------------------------------------------------------------------
    def test_compare_historical_performance(self):
        detail_df, summary_df = compare_historical_performance(
            income_stmt=self.synthetic_inc,
            balance_sheet=self.synthetic_bs,
            market_price=50.0,
            currency="USD",
        )
        self.assertEqual(len(detail_df), 3)
        self.assertFalse(summary_df.empty)

        # Check summary metrics
        metrics = summary_df["Metric"].tolist()
        self.assertIn("Revenue_Cr", metrics)
        self.assertIn("Net_Profit_Margin_%", metrics)
        self.assertIn("EPS", metrics)

    # -----------------------------------------------------------------------
    # Feature 7: Data Quality & Validation
    # -----------------------------------------------------------------------
    def test_audit_data_quality_clean(self):
        result = audit_financial_data_quality(
            income_stmt=self.synthetic_inc,
            balance_sheet=self.synthetic_bs,
            ticker="SYNTHETIC",
        )
        self.assertEqual(result["overall_status"], "PASS")
        self.assertEqual(result["severity_counts"]["CRITICAL"], 0)
        self.assertEqual(result["severity_counts"]["WARNING"], 0)

    def test_audit_data_quality_missing_metrics_and_period_mismatch(self):
        # Sparse period in income statement (only 1 row)
        sparse_inc = pd.DataFrame(
            {"2026-03-31": [1000.0], "2025-03-31": [np.nan]},
            index=["Total Revenue"]
        )
        # Balance sheet missing 2025-03-31
        bs_one_yr = pd.DataFrame(
            {"2026-03-31": [500.0, 1000.0, 500.0, 200.0]},
            index=["Total Debt", "Stockholders Equity", "Total Assets", "Current Liabilities"]
        )

        res = audit_financial_data_quality(
            income_stmt=sparse_inc,
            balance_sheet=bs_one_yr,
            ticker="SYNTH_SPARSE",
        )
        self.assertIn(res["overall_status"], ["CRITICAL", "WARNING"])
        # Must detect that 2025-03-31 exists in inc but missing in bs
        bs_mismatch = any("Balance_Sheet_Period" in i["Metric"] for i in res["issues"])
        self.assertTrue(bs_mismatch)

    def test_audit_data_quality_negative_values(self):
        # Legitimate loss (negative net income) vs invalid negative revenue
        inc_neg = pd.DataFrame(
            {
                "2026-03-31": [-500.0, -100.0],   # Negative revenue (CRITICAL) & loss (INFO)
            },
            index=["Total Revenue", "Net Income"]
        )
        res = audit_financial_data_quality(income_stmt=inc_neg, ticker="SYNTH_NEG")
        rev_issue = next((i for i in res["issues"] if i["Metric"] == "Revenue"), None)
        ni_issue  = next((i for i in res["issues"] if i["Metric"] == "Net_Income"), None)

        self.assertIsNotNone(rev_issue)
        self.assertEqual(rev_issue["Severity"], "CRITICAL")  # Negative revenue is critical error

        self.assertIsNotNone(ni_issue)
        self.assertEqual(ni_issue["Severity"], "INFO")       # Negative net income is legitimate loss

    def test_audit_data_quality_zero_division_risk(self):
        bs_zero = pd.DataFrame(
            {"2026-03-31": [100.0, 0.0, 500.0, 0.0]},
            index=["Total Debt", "Stockholders Equity", "Total Assets", "Current Liabilities"]
        )
        res = audit_financial_data_quality(income_stmt=self.synthetic_inc, balance_sheet=bs_zero)
        severities = [i["Severity"] for i in res["issues"]]
        self.assertIn("CRITICAL", severities)

    # -----------------------------------------------------------------------
    # Feature 8: Profitability Classification
    # -----------------------------------------------------------------------
    def test_classify_profitability_boundaries(self):
        # Boundaries: >=15 (Highly), 5-15 (Moderately), 0-5 (Low), <=0 (Not), None (Insufficient Data)
        self.assertEqual(classify_profitability_margin(20.0)[0], "Highly Profitable")
        self.assertEqual(classify_profitability_margin(15.0)[0], "Highly Profitable")
        self.assertEqual(classify_profitability_margin(14.99)[0], "Moderately Profitable")
        self.assertEqual(classify_profitability_margin(5.0)[0], "Moderately Profitable")
        self.assertEqual(classify_profitability_margin(4.99)[0], "Low Profitable")
        self.assertEqual(classify_profitability_margin(0.01)[0], "Low Profitable")
        self.assertEqual(classify_profitability_margin(0.0)[0], "Not Profitable")
        self.assertEqual(classify_profitability_margin(-5.0)[0], "Not Profitable")
        self.assertEqual(classify_profitability_margin(None)[0], "Insufficient Data")
        self.assertEqual(classify_profitability_margin(np.nan)[0], "Insufficient Data")

    def test_classify_profitability_multi_period(self):
        # Synthetic profitability analysis
        detail_df, summary_df = classify_profitability(
            income_stmt=self.synthetic_inc,
            ticker="SYNTHETIC",
        )
        self.assertEqual(len(detail_df), 3)
        self.assertFalse(summary_df.empty)

        # 2024: 100/1000 = 10% (Moderately)
        # 2025: 140/1200 = 11.67% (Moderately)
        # 2026: 210/1500 = 14% (Moderately)
        classes = detail_df["Classification"].tolist()
        self.assertEqual(classes, ["Moderately Profitable", "Moderately Profitable", "Moderately Profitable"])

        # Summary overall class
        summary_dict = dict(zip(summary_df["Item"], summary_df["Value"]))
        self.assertEqual(summary_dict["Overall Profitability Class"], "Moderately Profitable")

    # -----------------------------------------------------------------------
    # Feature 6: Peer Comparison
    # -----------------------------------------------------------------------
    def test_compare_peers_basic(self):
        target = {
            "ticker": "ALPHA",
            "name": "Alpha Corp",
            "currency": "INR",
            "sector": "Energy",
            "Net_Profit_Margin_%": 10.0,
            "ROE_%": 15.0,
            "Debt_to_Equity": 0.5,
            "Revenue_Cr": 1000.0,
            "Net_Income_Cr": 100.0,
            "PE_Ratio": 15.0,
        }
        peers = [
            {
                "ticker": "BETA",
                "name": "Beta Corp",
                "currency": "INR",
                "sector": "Energy",
                "Net_Profit_Margin_%": 12.0,
                "ROE_%": 18.0,
                "Debt_to_Equity": 0.4,
                "Revenue_Cr": 800.0,
                "Net_Income_Cr": 96.0,
                "PE_Ratio": 12.0,
            },
            {
                "ticker": "GAMMA",
                "name": "Gamma Corp",
                "currency": "INR",
                "sector": "Energy",
                "Net_Profit_Margin_%": 8.0,
                "ROE_%": 12.0,
                "Debt_to_Equity": 0.6,
                "Revenue_Cr": 1200.0,
                "Net_Income_Cr": 96.0,
                "PE_Ratio": 18.0,
            },
        ]

        result = compare_peers(target, peers, target_ticker="ALPHA")
        self.assertEqual(result["target_ticker"], "ALPHA")
        self.assertEqual(result["companies_compared"], 3)
        self.assertEqual(result["peer_count"], 2)

        # Check target identification
        companies = result["companies"]
        self.assertTrue(companies[0]["is_target"])
        self.assertFalse(companies[1]["is_target"])
        self.assertFalse(companies[2]["is_target"])

        # Check peer average for Net Profit Margin: (12 + 8) / 2 = 10.0%
        npm_bench = result["peer_benchmarks"]["Net_Profit_Margin_%"]
        self.assertAlmostEqual(npm_bench["peer_average"], 10.0, places=2)
        self.assertAlmostEqual(npm_bench["peer_median"], 10.0, places=2)
        self.assertAlmostEqual(npm_bench["peer_min"], 8.0, places=2)
        self.assertAlmostEqual(npm_bench["peer_max"], 12.0, places=2)
        # Ranks: Beta=12% (1), Alpha=10% (2), Gamma=8% (3)
        self.assertEqual(npm_bench["target_rank"], 2)

        # Check ranking for Debt to Equity (direction="Lower": lower is better)
        # Beta=0.4 (1), Alpha=0.5 (2), Gamma=0.6 (3)
        de_bench = result["peer_benchmarks"]["Debt_to_Equity"]
        self.assertEqual(de_bench["target_rank"], 2)

    def test_compare_peers_single_peer(self):
        target = {"ticker": "ALPHA", "currency": "USD", "Operating_Margin_%": 15.0}
        peers  = [{"ticker": "BETA", "currency": "USD", "Operating_Margin_%": 20.0}]

        res = compare_peers(target, peers)
        self.assertEqual(res["peer_count"], 1)
        self.assertAlmostEqual(res["peer_benchmarks"]["Operating_Margin_%"]["peer_average"], 20.0)

    def test_compare_peers_empty_list(self):
        target = {"ticker": "SOLO", "currency": "USD", "Net_Profit_Margin_%": 10.0}
        res = compare_peers(target, [])
        self.assertEqual(res["peer_count"], 0)
        self.assertIn("No peer companies were provided", res["warnings"][0])
        self.assertIsNone(res["peer_benchmarks"]["Net_Profit_Margin_%"]["peer_average"])

    def test_compare_peers_currency_mismatch(self):
        target = {"ticker": "TGT_IN", "currency": "INR", "Revenue_Cr": 1000.0, "Net_Profit_Margin_%": 10.0}
        peer_us = {"ticker": "PEER_US", "currency": "USD", "Revenue_Cr": 500.0, "Net_Profit_Margin_%": 14.0}

        res = compare_peers(target, [peer_us])
        # Warning must be issued
        curr_warnings = [w for w in res["warnings"] if "Currency Mismatch" in w]
        self.assertTrue(len(curr_warnings) > 0)

        # Monetary peer average (Revenue_Cr) must NOT average across USD and INR!
        self.assertIsNone(res["peer_benchmarks"]["Revenue_Cr"]["peer_average"])

        # Ratio peer average (Net_Profit_Margin_%) CAN be compared safely
        self.assertAlmostEqual(res["peer_benchmarks"]["Net_Profit_Margin_%"]["peer_average"], 14.0)

    def test_compare_peers_sector_mismatch(self):
        target = {"ticker": "OIL_CO", "sector": "Energy", "Net_Profit_Margin_%": 8.0}
        peer   = {"ticker": "TECH_CO", "sector": "Technology", "Net_Profit_Margin_%": 25.0}

        res = compare_peers(target, [peer])
        sec_warnings = [w for w in res["warnings"] if "Cross-Sector" in w]
        self.assertTrue(len(sec_warnings) > 0)

    def test_compare_peers_json_serializable(self):
        target = {"ticker": "TEST", "currency": "INR", "Net_Profit_Margin_%": 10.0, "Revenue_Cr": np.nan}
        peer   = {"ticker": "PEER", "currency": "INR", "Net_Profit_Margin_%": None}

        res = compare_peers(target, [peer])
        # Must serialize cleanly to JSON string without errors
        serialized = json.dumps(res)
        self.assertIn('"target_ticker": "TEST"', serialized)

    def test_run_fundamental_analysis_with_peers(self):
        peer_list = [
            {"ticker": "PEER1", "currency": "INR", "Net_Profit_Margin_%": 12.0, "ROE_%": 14.0},
            {"ticker": "PEER2", "currency": "INR", "Net_Profit_Margin_%": 8.0,  "ROE_%": 10.0},
        ]
        result = run_fundamental_analysis(
            self.synthetic_inc,
            self.synthetic_bs,
            market_price=50.0,
            ticker="SYNTHETIC",
            peer_companies=peer_list,
        )
        self.assertIn("peer_comparison", result)
        self.assertIsNotNone(result["peer_comparison"])
        self.assertEqual(result["peer_comparison"]["target_ticker"], "SYNTHETIC")
        self.assertEqual(result["peer_comparison"]["peer_count"], 2)

    # -----------------------------------------------------------------------
    # Master Runner (Updated with Features 7 & 8)
    # -----------------------------------------------------------------------
    def test_run_fundamental_analysis(self):
        result = run_fundamental_analysis(
            self.synthetic_inc,
            self.synthetic_bs,
            market_price=50.0,
            ticker="SYNTHETIC",
        )
        expected_keys = [
            "ticker", "currency",
            "revenue_earnings", "profitability", "debt_stability",
            "financial_ratios", "historical_detail", "historical_summary",
            "data_quality", "profitability_classification"
        ]
        for k in expected_keys:
            self.assertIn(k, result)

        self.assertIsInstance(result["data_quality"], dict)
        self.assertIn("issues", result["data_quality"])
        self.assertIn("overall_status", result["data_quality"])

        self.assertIsInstance(result["profitability_classification"], dict)
        self.assertIn("detail", result["profitability_classification"])
        self.assertIn("summary", result["profitability_classification"])


class TestRelianceParityValidation(unittest.TestCase):
    """
    Validates that core.py produces exact/near-exact parity when fed Reliance raw statements
    compared to the pre-existing processed CSV files generated in Features 1-5.
    """

    @classmethod
    def setUpClass(cls):
        # Locate project root and processed CSV directory
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parents[3]
        cls.data_dir = project_root / "backend" / "ml" / "financial_agent" / "data" / "processed"

        inc_path = cls.data_dir / "reliance_annual_income_statement.csv"
        bs_path  = cls.data_dir / "reliance_annual_balance_sheet.csv"

        if not (inc_path.exists() and bs_path.exists()):
            raise unittest.SkipTest("Reliance raw statement CSVs not available for parity check")

        cls.inc_raw = pd.read_csv(inc_path, index_col=0)
        cls.bs_raw  = pd.read_csv(bs_path, index_col=0)

    def test_revenue_earnings_parity(self):
        expected_csv = self.data_dir / "reliance_revenue_earnings_analysis.csv"
        if not expected_csv.exists():
            self.skipTest("reliance_revenue_earnings_analysis.csv missing")

        expected_df = pd.read_csv(expected_csv)
        actual_df   = analyze_revenue_earnings(self.inc_raw)

        self.assertEqual(len(actual_df), len(expected_df))
        for col in ["Revenue", "Net_Income", "Revenue_Growth_%", "Earnings_Growth_%"]:
            for i in range(len(expected_df)):
                exp_v = expected_df.loc[i, col]
                act_v = actual_df.loc[i, col]
                if pd.isna(exp_v):
                    self.assertTrue(pd.isna(act_v), f"Expected NaN at row {i} col {col}")
                else:
                    self.assertAlmostEqual(act_v, exp_v, places=3, msg=f"Mismatch at row {i} col {col}")

    def test_profitability_parity(self):
        expected_csv = self.data_dir / "reliance_profitability_analysis.csv"
        if not expected_csv.exists():
            self.skipTest("reliance_profitability_analysis.csv missing")

        expected_df = pd.read_csv(expected_csv)
        actual_df   = analyze_profitability(self.inc_raw)

        self.assertEqual(len(actual_df), len(expected_df))
        for col in ["Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%", "EBITDA_Margin_%"]:
            for i in range(len(expected_df)):
                exp_v = expected_df.loc[i, col]
                act_v = actual_df.loc[i, col]
                if pd.isna(exp_v):
                    self.assertTrue(pd.isna(act_v), f"Expected NaN at row {i} col {col}")
                else:
                    self.assertAlmostEqual(act_v, exp_v, places=3, msg=f"Mismatch at row {i} col {col}")

    def test_debt_stability_parity(self):
        expected_csv = self.data_dir / "reliance_debt_stability_analysis.csv"
        if not expected_csv.exists():
            self.skipTest("reliance_debt_stability_analysis.csv missing")

        expected_df = pd.read_csv(expected_csv)
        actual_df   = analyze_debt_stability(self.bs_raw)

        self.assertEqual(len(actual_df), len(expected_df))
        for col in ["Debt_to_Equity_Ratio", "Debt_to_Assets_Ratio", "Current_Ratio", "Cash_to_Debt_Ratio", "Net_Debt_to_Assets_Ratio"]:
            for i in range(len(expected_df)):
                exp_v = expected_df.loc[i, col]
                act_v = actual_df.loc[i, col]
                if pd.isna(exp_v):
                    self.assertTrue(pd.isna(act_v), f"Expected NaN at row {i} col {col}")
                else:
                    self.assertAlmostEqual(act_v, exp_v, places=4, msg=f"Mismatch at row {i} col {col}")

    def test_financial_ratios_parity(self):
        expected_csv = self.data_dir / "reliance_financial_ratios_analysis.csv"
        if not expected_csv.exists():
            self.skipTest("reliance_financial_ratios_analysis.csv missing")

        expected_df = pd.read_csv(expected_csv)
        actual_df   = analyze_financial_ratios(self.inc_raw, self.bs_raw, market_price=1351.0, price_date="2026-11-23")

        self.assertEqual(len(actual_df), len(expected_df))
        for col in ["ROE_%", "EPS", "Book_Value_Per_Share", "PE_Ratio", "PB_Ratio"]:
            for i in range(len(expected_df)):
                exp_v = expected_df.loc[i, col]
                act_v = actual_df.loc[i, col]
                if pd.isna(exp_v):
                    self.assertTrue(pd.isna(act_v), f"Expected NaN at row {i} col {col}")
                else:
                    self.assertAlmostEqual(act_v, exp_v, places=3, msg=f"Mismatch at row {i} col {col}")

    def test_data_quality_parity(self):
        """Verify core.audit_financial_data_quality detects the same critical/warning issues as Feature 7."""
        expected_csv = self.data_dir / "financial_data_quality_report.csv"
        if not expected_csv.exists():
            self.skipTest("financial_data_quality_report.csv missing")

        expected_df = pd.read_csv(expected_csv)
        prof_df = analyze_profitability(self.inc_raw)
        rat_df  = analyze_financial_ratios(self.inc_raw, self.bs_raw, market_price=1351.0)
        res = audit_financial_data_quality(
            self.inc_raw,
            self.bs_raw,
            derived_data={"profitability": prof_df, "financial_ratios": rat_df},
            ticker="RELIANCE.NS"
        )

        actual_issues = res["issues"]
        # Verify both detect the 2022-03-31 Core_Metrics critical issue
        crit_actual = [i for i in actual_issues if i["Severity"] == "CRITICAL"]
        crit_expected = expected_df[expected_df["Severity"] == "CRITICAL"]
        self.assertEqual(len(crit_actual), len(crit_expected))
        self.assertEqual(crit_actual[0]["Period"], "2022-03-31")

        # Verify warning detection (Balance sheet missing 2022 period)
        warn_actual = [i for i in actual_issues if i["Severity"] == "WARNING"]
        warn_expected = expected_df[expected_df["Severity"] == "WARNING"]
        self.assertEqual(len(warn_actual), len(warn_expected))
        self.assertEqual(warn_actual[0]["Period"], "2022-03-31")

    def test_profitability_classification_parity(self):
        """Verify core.classify_profitability produces the exact same tiers as Feature 8."""
        expected_csv = self.data_dir / "profitability_classification.csv"
        if not expected_csv.exists():
            self.skipTest("profitability_classification.csv missing")

        expected_df = pd.read_csv(expected_csv)
        prof_df = analyze_profitability(self.inc_raw)
        detail_df, summary_df = classify_profitability(
            profitability_df=prof_df,
            ticker="RELIANCE.NS",
        )

        self.assertEqual(len(detail_df), len(expected_df))
        for i in range(len(expected_df)):
            self.assertEqual(detail_df.loc[i, "Classification"], expected_df.loc[i, "Classification"])
            exp_npm = expected_df.loc[i, "Net_Profit_Margin_%"]
            act_npm = detail_df.loc[i, "Net_Profit_Margin_%"]
            if pd.isna(exp_npm):
                self.assertTrue(pd.isna(act_npm))
            else:
                self.assertAlmostEqual(act_npm, exp_npm, places=3)

        # Executive class must match
        summary_dict = dict(zip(summary_df["Item"], summary_df["Value"]))
        self.assertEqual(summary_dict["Overall Profitability Class"], "Moderately Profitable")
        self.assertEqual(summary_dict["Latest Net Profit Margin (%)"], "7.64%")

    def test_peer_comparison_parity(self):
        """Verify core.compare_peers produces exact parity with reliance_peer_comparison.csv."""
        expected_csv = self.data_dir / "reliance_peer_comparison.csv"
        if not expected_csv.exists():
            self.skipTest("reliance_peer_comparison.csv missing")

        expected_df = pd.read_csv(expected_csv)
        # Row 0 is RELIANCE.NS, rows 1-6 are the 6 peers
        target_series = expected_df.iloc[0]
        peer_df = expected_df.iloc[1:].copy()

        res = compare_peers(
            target_company=target_series,
            peer_companies=peer_df,
            target_ticker="RELIANCE.NS",
        )

        self.assertEqual(res["target_ticker"], "RELIANCE.NS")
        self.assertEqual(res["companies_compared"], 7)
        self.assertEqual(res["peer_count"], 6)

        # Check exact metric parity for all 7 companies
        comp_table = pd.DataFrame(res["comparison_table"])
        self.assertEqual(len(comp_table), len(expected_df))

        metrics_to_check = [
            "Revenue_Cr", "Revenue_Growth_%", "Net_Income_Cr", "Net_Income_Growth_%",
            "Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%",
            "EBITDA_Margin_%", "ROE_%", "Debt_to_Equity", "Debt_to_Assets",
            "Current_Ratio", "EPS", "PE_Ratio", "PB_Ratio"
        ]

        for _, exp_row in expected_df.iterrows():
            ticker = exp_row["Ticker"]
            match = comp_table[comp_table["Ticker"] == ticker]
            self.assertFalse(match.empty, f"Ticker {ticker} missing from comparison table")
            act_row = match.iloc[0]

            for m in metrics_to_check:
                exp_v = exp_row[m]
                act_v = act_row[m]
                if pd.isna(exp_v):
                    self.assertTrue(pd.isna(act_v) or act_v is None, f"{ticker} {m} expected NaN")
                else:
                    self.assertAlmostEqual(
                        float(act_v), float(exp_v), places=3,
                        msg=f"{ticker} {m} mismatch: act={act_v} vs exp={exp_v}"
                    )


if __name__ == "__main__":
    unittest.main()
