"""
test_utils.py
--------------
Unit tests for shared Financial Agent utilities (backend/ml/financial_agent/utils.py).

Uses Python's standard unittest library and small synthetic test data.
Completely decoupled from live market data or external CSVs.
"""

import math
import unittest
import numpy as np
import pandas as pd

try:
    from ml.financial_agent.utils import (
        is_valid_number,
        safe_divide,
        safe_pct_ratio,
        safe_pct_change,
        safe_diff,
        get_metric,
        normalize_periods,
        scale_currency_amount,
        format_currency_display,
        trend_direction,
    )
except ImportError:
    from backend.ml.financial_agent.utils import (
        is_valid_number,
        safe_divide,
        safe_pct_ratio,
        safe_pct_change,
        safe_diff,
        get_metric,
        normalize_periods,
        scale_currency_amount,
        format_currency_display,
        trend_direction,
    )


class TestFinancialUtils(unittest.TestCase):

    # -----------------------------------------------------------------------
    # 1. safe_divide tests
    # -----------------------------------------------------------------------
    def test_safe_divide_normal(self):
        self.assertEqual(safe_divide(100, 20), 5.0)
        self.assertEqual(safe_divide(10, 3, decimals=2), 3.33)
        self.assertEqual(safe_divide(-50, 10), -5.0)

    def test_safe_divide_zero_denominator(self):
        # Must return None or default, NEVER 0.0 or raise ZeroDivisionError
        self.assertIsNone(safe_divide(100, 0))
        self.assertIsNone(safe_divide(0, 0))
        self.assertEqual(safe_divide(100, 0, default="N/A"), "N/A")

    def test_safe_divide_missing_and_nan(self):
        self.assertIsNone(safe_divide(None, 50))
        self.assertIsNone(safe_divide(50, None))
        self.assertIsNone(safe_divide(np.nan, 50))
        self.assertIsNone(safe_divide(50, np.nan))
        self.assertIsNone(safe_divide(float("nan"), 10))
        self.assertIsNone(safe_divide(10, float("inf")))

    # -----------------------------------------------------------------------
    # 2. safe_pct_ratio tests (Margins & ROE)
    # -----------------------------------------------------------------------
    def test_safe_pct_ratio(self):
        # 25 / 100 * 100 = 25.0%
        self.assertEqual(safe_pct_ratio(25, 100), 25.0)
        self.assertEqual(safe_pct_ratio(80775, 1057219, decimals=2), 7.64)
        self.assertIsNone(safe_pct_ratio(25, 0))
        self.assertIsNone(safe_pct_ratio(None, 100))

    # -----------------------------------------------------------------------
    # 3. safe_pct_change tests (YoY growth)
    # -----------------------------------------------------------------------
    def test_safe_pct_change_positive(self):
        # (120 - 100) / 100 * 100 = +20%
        self.assertEqual(safe_pct_change(120, 100), 20.0)

    def test_safe_pct_change_negative(self):
        # (80 - 100) / 100 * 100 = -20%
        self.assertEqual(safe_pct_change(80, 100), -20.0)

    def test_safe_pct_change_zero_previous(self):
        # Percentage growth from base 0 is undefined
        self.assertIsNone(safe_pct_change(100, 0))
        self.assertEqual(safe_pct_change(100, 0, default="Undefined"), "Undefined")

    def test_safe_pct_change_missing_and_nan(self):
        self.assertIsNone(safe_pct_change(None, 100))
        self.assertIsNone(safe_pct_change(100, None))
        self.assertIsNone(safe_pct_change(np.nan, 100))
        self.assertIsNone(safe_pct_change(100, np.nan))

    # -----------------------------------------------------------------------
    # 4. get_metric tests (Fallback extraction)
    # -----------------------------------------------------------------------
    def test_get_metric_row_format(self):
        # Synthetic yfinance format: rows = metrics, columns = periods
        df = pd.DataFrame(
            {
                "2026-03-31": [1000.0, np.nan, 250.0],
                "2025-03-31": [900.0, 900.0, 200.0],
            },
            index=["Operating Revenue", "Total Revenue", "Net Income"],
        )

        # Primary name "Total Revenue" is NaN for 2026, fallback "Operating Revenue" is 1000.0
        val = get_metric(df, ["Total Revenue", "Operating Revenue"], period="2026-03-31")
        self.assertEqual(val, 1000.0)

        # Direct primary hit
        val_ni = get_metric(df, ["Net Income"], period="2026-03-31")
        self.assertEqual(val_ni, 250.0)

        # Missing metric returns default
        val_missing = get_metric(df, ["Nonexistent Metric", "Missing Key"], default="Not Found")
        self.assertEqual(val_missing, "Not Found")

    def test_get_metric_column_format(self):
        # Processed CSV format: columns = metrics, rows = periods
        df = pd.DataFrame({
            "Financial_Year": ["2025-03-31", "2026-03-31"],
            "Revenue": [9000.0, 10500.0],
            "Net_Profit_Margin_%": [7.2, 7.64],
        })

        val = get_metric(df, ["Net_Profit_Margin_%", "Net Margin"], period="2026-03-31")
        self.assertEqual(val, 7.64)

    def test_get_metric_dict(self):
        flat_data = {"Rev": 500.0, "EPS": 12.5}
        self.assertEqual(get_metric(flat_data, ["Revenue", "Rev"]), 500.0)
        self.assertIsNone(get_metric(flat_data, ["Unknown"]))

    # -----------------------------------------------------------------------
    # 5. normalize_periods tests
    # -----------------------------------------------------------------------
    def test_normalize_periods_sorting(self):
        # Unsorted list with mixed types & duplicates
        raw = ["2025-03-31", "2023-03-31", "2026-03-31", "2024-03-31", "2023-03-31", None, "invalid_date"]
        normalized = normalize_periods(raw, descending=False)
        expected = ["2023-03-31", "2024-03-31", "2025-03-31", "2026-03-31"]
        self.assertEqual(normalized, expected)

    def test_normalize_periods_descending(self):
        raw = ["2023-03-31", "2026-03-31", "2024-03-31"]
        normalized = normalize_periods(raw, descending=True)
        self.assertEqual(normalized, ["2026-03-31", "2024-03-31", "2023-03-31"])

    # -----------------------------------------------------------------------
    # 6. Currency scaling & formatting tests
    # -----------------------------------------------------------------------
    def test_scale_currency_inr(self):
        # 10,000,000 INR = 1.00 Crore
        scaled, unit = scale_currency_amount(10_000_000, currency="INR", target_scale="crore")
        self.assertEqual(scaled, 1.0)
        self.assertEqual(unit, "INR Cr")

        # Missing amount returns None
        scaled_none, unit_none = scale_currency_amount(None, currency="INR")
        self.assertIsNone(scaled_none)
        self.assertEqual(unit_none, "INR")

    def test_scale_currency_usd(self):
        # 15,000,000,000 USD = 15.00 B
        scaled_b, unit_b = scale_currency_amount(15_000_000_000, currency="USD")
        self.assertEqual(scaled_b, 15.0)
        self.assertEqual(unit_b, "USD B")

        # 25,000,000 USD = 25.00 M
        scaled_m, unit_m = scale_currency_amount(25_000_000, currency="USD")
        self.assertEqual(scaled_m, 25.0)
        self.assertEqual(unit_m, "USD M")

    def test_format_currency_display(self):
        # Display formatted strings
        inr_disp = format_currency_display(80_775_000_000, currency="INR", target_scale="crore")
        self.assertEqual(inr_disp, "₹8,077.50 Cr")

        usd_disp = format_currency_display(2_500_000_000, currency="USD")
        self.assertEqual(usd_disp, "$2.50 B")

        # Missing value shows placeholder
        self.assertEqual(format_currency_display(None), "—")
        self.assertEqual(format_currency_display(np.nan, placeholder="N/A"), "N/A")

    # -----------------------------------------------------------------------
    # 7. trend_direction tests
    # -----------------------------------------------------------------------
    def test_trend_direction(self):
        # Strictly improving
        self.assertEqual(trend_direction([10.0, 12.0, 15.0]), "Improving")

        # Strictly declining
        self.assertEqual(trend_direction([25.0, 20.0, 18.0]), "Declining")

        # Stable (movements <= 0.05)
        self.assertEqual(trend_direction([10.0, 10.02, 10.01]), "Stable")

        # Mixed
        self.assertEqual(trend_direction([10.0, 14.0, 11.0, 15.0]), "Mixed")

        # Insufficient data
        self.assertEqual(trend_direction([10.0]), "Insufficient Data")
        self.assertEqual(trend_direction([None, np.nan]), "Insufficient Data")


if __name__ == "__main__":
    unittest.main()
