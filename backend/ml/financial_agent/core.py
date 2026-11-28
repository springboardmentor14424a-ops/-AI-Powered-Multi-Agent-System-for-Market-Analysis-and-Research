"""
core.py
-------
Module 3 – Financial Agent | In-Memory Core Financial Analysis Engine

Implements pure in-memory analytical functions for Features 1–5:
  1. Revenue & Earnings Analysis
  2. Profitability Analysis
  3. Debt & Financial Stability Analysis
  4. Financial Ratios Analysis
  5. Historical Financial Performance Comparison

Design Principles:
  - Zero hardcoded tickers or company names.
  - Zero hardcoded file paths or CSV read/write operations.
  - Zero network/yfinance calls (pure computational engine).
  - Handles missing/sparse data gracefully without silent zero-substitution.
  - Uses shared utilities from `backend.ml.financial_agent.utils`.
  - Structured output ready for FastAPI serialization or downstream agent consumption.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
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
        trend_direction,
    )


# ===========================================================================
# HELPER: PERIOD EXTRACTION & STATEMENT ORIENTATION
# ===========================================================================

def _extract_statement_periods(stmt: pd.DataFrame) -> List[str]:
    """
    Extract chronological financial periods ('YYYY-MM-DD') from a statement DataFrame.
    Handles both:
      - yfinance layout: rows = metrics, columns = dates
      - Tabular layout: rows = periods (with 'Financial_Year' or DatetimeIndex)
    """
    if stmt is None or stmt.empty:
        return []

    # Case 1: Tabular with 'Financial_Year' column
    if "Financial_Year" in stmt.columns:
        return normalize_periods(stmt["Financial_Year"].tolist(), descending=False)

    # Case 2: yfinance layout where columns are date strings / Timestamps
    date_cols = [c for c in stmt.columns if not str(c).startswith("Unnamed")]
    return normalize_periods(date_cols, descending=False)


def _trend_label_for_delta(delta: Optional[float], min_delta: float = 0.0) -> str:
    """Classify single period-over-period delta into status."""
    if delta is None or pd.isna(delta):
        return "Insufficient Data"
    if delta > min_delta:
        return "Improving"
    elif delta < -min_delta:
        return "Declining"
    else:
        return "Stable"


# ===========================================================================
# FEATURE 1: REVENUE & EARNINGS ANALYSIS
# ===========================================================================

def analyze_revenue_earnings(income_stmt: pd.DataFrame) -> pd.DataFrame:
    """
    Perform Revenue & Earnings Growth and Trend Analysis across available years.

    Metrics:
      - Revenue (Total Revenue, fallback Operating Revenue)
      - Net_Income (Net Income, fallback Normalized Income)
      - Revenue_Growth_%: ((Revenue - Prev_Revenue) / abs(Prev_Revenue)) * 100
      - Earnings_Growth_%: ((Net_Income - Prev_Net_Income) / abs(Prev_Net_Income)) * 100
      - Revenue_Trend: absolute change in Revenue
      - Earnings_Trend: absolute change in Net_Income

    Returns:
      pd.DataFrame sorted chronologically by Financial_Year.
    """
    periods = _extract_statement_periods(income_stmt)
    rows: List[Dict[str, Any]] = []

    for p in periods:
        rev = get_metric(income_stmt, ["Total Revenue", "Operating Revenue"], period=p)
        ni  = get_metric(income_stmt, ["Net Income", "Normalized Income", "Net Income Common Stockholders"], period=p)

        rows.append({
            "Financial_Year": p,
            "Revenue": rev,
            "Net_Income": ni,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=[
            "Financial_Year", "Revenue", "Net_Income",
            "Revenue_Growth_%", "Earnings_Growth_%",
            "Revenue_Trend", "Earnings_Trend"
        ])

    # Calculate growth and trends chronologically
    df["Revenue_Growth_%"] = np.nan
    df["Earnings_Growth_%"] = np.nan
    df["Revenue_Trend"] = np.nan
    df["Earnings_Trend"] = np.nan

    for i in range(1, len(df)):
        cur_rev  = df.loc[i,     "Revenue"]
        prev_rev = df.loc[i - 1, "Revenue"]
        cur_ni   = df.loc[i,     "Net_Income"]
        prev_ni  = df.loc[i - 1, "Net_Income"]

        df.loc[i, "Revenue_Growth_%"]  = safe_pct_change(cur_rev, prev_rev)
        df.loc[i, "Earnings_Growth_%"] = safe_pct_change(cur_ni, prev_ni)
        df.loc[i, "Revenue_Trend"]     = safe_diff(cur_rev, prev_rev, decimals=2)
        df.loc[i, "Earnings_Trend"]    = safe_diff(cur_ni, prev_ni, decimals=2)

    return df


# ===========================================================================
# FEATURE 2: PROFITABILITY ANALYSIS
# ===========================================================================

def analyze_profitability(income_stmt: pd.DataFrame) -> pd.DataFrame:
    """
    Perform Profitability Margins & Operational Trend Analysis.

    Metrics:
      - Revenue, Gross_Profit, Operating_Income, Net_Income, EBITDA
      - Gross_Profit_Margin_%: (Gross_Profit / Revenue) * 100
      - Operating_Margin_%:    (Operating_Income / Revenue) * 100
      - Net_Profit_Margin_%:   (Net_Income / Revenue) * 100
      - EBITDA_Margin_%:       (EBITDA / Revenue) * 100
      - Margin changes and status labels (Improving / Declining / Stable / Insufficient Data)

    Returns:
      pd.DataFrame sorted chronologically by Financial_Year.
    """
    periods = _extract_statement_periods(income_stmt)
    rows: List[Dict[str, Any]] = []

    for p in periods:
        rev = get_metric(income_stmt, ["Total Revenue", "Operating Revenue"], period=p)
        gp  = get_metric(income_stmt, ["Gross Profit"], period=p)
        op  = get_metric(income_stmt, ["Operating Income"], period=p)
        ni  = get_metric(income_stmt, ["Net Income", "Normalized Income"], period=p)

        # EBITDA direct or derived from EBIT + Depreciation
        eb = get_metric(income_stmt, ["EBITDA", "Normalized EBITDA"], period=p)
        if eb is None:
            ebit = get_metric(income_stmt, ["EBIT"], period=p)
            depr = get_metric(income_stmt, ["Reconciled Depreciation"], period=p)
            if ebit is not None and depr is not None:
                eb = ebit + depr

        gpm = safe_pct_ratio(gp, rev)
        opm = safe_pct_ratio(op, rev)
        npm = safe_pct_ratio(ni, rev)
        ebm = safe_pct_ratio(eb, rev)

        rows.append({
            "Financial_Year":         p,
            "Revenue":                rev,
            "Gross_Profit":           gp,
            "Operating_Income":       op,
            "Net_Income":             ni,
            "EBITDA":                 eb,
            "Gross_Profit_Margin_%":  gpm,
            "Operating_Margin_%":     opm,
            "Net_Profit_Margin_%":    npm,
            "EBITDA_Margin_%":        ebm,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()

    df["Gross_Margin_Change"] = np.nan
    df["Operating_Margin_Change"] = np.nan
    df["Net_Margin_Change"] = np.nan
    df["Gross_Margin_Status"] = "Insufficient Data"
    df["Operating_Margin_Status"] = "Insufficient Data"
    df["Net_Margin_Status"] = "Insufficient Data"

    for i in range(1, len(df)):
        cur_gp  = df.loc[i,     "Gross_Profit_Margin_%"]
        prev_gp = df.loc[i - 1, "Gross_Profit_Margin_%"]
        cur_op  = df.loc[i,     "Operating_Margin_%"]
        prev_op = df.loc[i - 1, "Operating_Margin_%"]
        cur_np  = df.loc[i,     "Net_Profit_Margin_%"]
        prev_np = df.loc[i - 1, "Net_Profit_Margin_%"]

        g_chg = safe_diff(cur_gp, prev_gp, decimals=6)
        o_chg = safe_diff(cur_op, prev_op, decimals=6)
        n_chg = safe_diff(cur_np, prev_np, decimals=6)

        df.loc[i, "Gross_Margin_Change"]     = g_chg
        df.loc[i, "Operating_Margin_Change"] = o_chg
        df.loc[i, "Net_Margin_Change"]       = n_chg

        df.loc[i, "Gross_Margin_Status"]     = _trend_label_for_delta(g_chg)
        df.loc[i, "Operating_Margin_Status"] = _trend_label_for_delta(o_chg)
        df.loc[i, "Net_Margin_Status"]       = _trend_label_for_delta(n_chg)

    return df


# ===========================================================================
# FEATURE 3: DEBT & FINANCIAL STABILITY ANALYSIS
# ===========================================================================

def analyze_debt_stability(balance_sheet: pd.DataFrame) -> pd.DataFrame:
    """
    Perform Balance Sheet Leverage & Liquidity Stability Analysis.

    Metrics:
      - Total_Debt, Net_Debt, Total_Assets, Stockholders_Equity,
        Current_Assets, Current_Liabilities, Cash_And_Cash_Equivalents
      - Debt_to_Equity_Ratio     = Total Debt / Stockholders Equity
      - Debt_to_Assets_Ratio     = Total Debt / Total Assets
      - Current_Ratio            = Current Assets / Current Liabilities
      - Cash_to_Debt_Ratio       = Cash And Cash Equivalents / Total Debt
      - Net_Debt_to_Assets_Ratio = Net Debt / Total Assets

    Returns:
      pd.DataFrame sorted chronologically by Financial_Year.
    """
    periods = _extract_statement_periods(balance_sheet)
    rows: List[Dict[str, Any]] = []

    for p in periods:
        td = get_metric(balance_sheet, ["Total Debt"], period=p)
        nd = get_metric(balance_sheet, ["Net Debt"], period=p)
        ta = get_metric(balance_sheet, ["Total Assets"], period=p)
        eq = get_metric(balance_sheet, ["Stockholders Equity"], period=p)
        ca = get_metric(balance_sheet, ["Current Assets"], period=p)
        cl = get_metric(balance_sheet, ["Current Liabilities"], period=p)
        cash = get_metric(balance_sheet, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], period=p)

        de_ratio   = safe_divide(td, eq, decimals=6)
        da_ratio   = safe_divide(td, ta, decimals=6)
        curr_ratio = safe_divide(ca, cl, decimals=6)
        cd_ratio   = safe_divide(cash, td, decimals=6)
        nda_ratio  = safe_divide(nd, ta, decimals=6)

        rows.append({
            "Financial_Year":             p,
            "Total_Debt":                 td,
            "Net_Debt":                   nd,
            "Total_Assets":               ta,
            "Stockholders_Equity":        eq,
            "Current_Assets":             ca,
            "Current_Liabilities":        cl,
            "Cash_And_Cash_Equivalents":  cash,
            "Debt_to_Equity_Ratio":       de_ratio,
            "Debt_to_Assets_Ratio":       da_ratio,
            "Current_Ratio":              curr_ratio,
            "Cash_to_Debt_Ratio":         cd_ratio,
            "Net_Debt_to_Assets_Ratio":   nda_ratio,
        })

    return pd.DataFrame(rows)


# ===========================================================================
# FEATURE 4: FINANCIAL RATIOS ANALYSIS (ROE, EPS, BVPS, P/E, P/B)
# ===========================================================================

def analyze_financial_ratios(
    income_stmt: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    market_price: Optional[float] = None,
    price_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Calculate Return on Equity, Per-Share Metrics, and Point-in-Time Valuation Ratios.

    Metrics:
      - ROE_%                = (Net Income / Stockholders Equity) * 100
      - EPS                  = Net Income / Ordinary Shares Number
      - Book_Value_Per_Share = Stockholders Equity / Ordinary Shares Number
      - PE_Ratio             = Latest Stock Price / Latest EPS (on latest valid year only)
      - PB_Ratio             = Latest Stock Price / Latest BVPS (on latest valid year only)

    Returns:
      pd.DataFrame sorted chronologically by Financial_Year.
    """
    inc_periods = set(_extract_statement_periods(income_stmt))
    bs_periods  = set(_extract_statement_periods(balance_sheet))
    all_periods = normalize_periods(inc_periods.union(bs_periods), descending=False)

    rows: List[Dict[str, Any]] = []

    for p in all_periods:
        ni     = get_metric(income_stmt, ["Net Income", "Normalized Income"], period=p)
        equity = get_metric(balance_sheet, ["Stockholders Equity"], period=p)
        shares = get_metric(balance_sheet, ["Ordinary Shares Number", "Share Issued"], period=p)
        if shares is None:
            shares = get_metric(income_stmt, ["Diluted Average Shares", "Basic Average Shares"], period=p)

        roe = safe_pct_ratio(ni, equity, decimals=6)
        eps = safe_divide(ni, shares, decimals=6)
        bvps = safe_divide(equity, shares, decimals=6)

        rows.append({
            "Financial_Year":          p,
            "Net_Income":              ni,
            "Stockholders_Equity":     equity,
            "Ordinary_Shares_Number":  shares,
            "ROE_%":                   roe,
            "EPS":                     eps,
            "Book_Value_Per_Share":    bvps,
            "Latest_Stock_Price":      np.nan,
            "Stock_Price_Date":        None,
            "PE_Ratio":                np.nan,
            "PB_Ratio":                np.nan,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Ensure Stock_Price_Date column can hold string dates
    df["Stock_Price_Date"] = df["Stock_Price_Date"].astype(object)

    # If market price is available, populate valuation multiples on the latest valid FY row
    if is_valid_number(market_price):
        price = float(market_price)
        valid_years = df[df["EPS"].notna() & df["Book_Value_Per_Share"].notna()]
        if not valid_years.empty:
            latest_idx = valid_years.index[-1]
            latest_eps  = df.loc[latest_idx, "EPS"]
            latest_bvps = df.loc[latest_idx, "Book_Value_Per_Share"]

            pe = safe_divide(price, latest_eps, decimals=6)
            pb = safe_divide(price, latest_bvps, decimals=6)

            df.loc[latest_idx, "Latest_Stock_Price"] = price
            df.loc[latest_idx, "Stock_Price_Date"]   = price_date or "Latest"
            df.loc[latest_idx, "PE_Ratio"]           = pe
            df.loc[latest_idx, "PB_Ratio"]           = pb

    return df


# ===========================================================================
# FEATURE 5: HISTORICAL PERFORMANCE COMPARISON
# ===========================================================================

def compare_historical_performance(
    revenue_df: Optional[pd.DataFrame] = None,
    profitability_df: Optional[pd.DataFrame] = None,
    ratios_df: Optional[pd.DataFrame] = None,
    income_stmt: Optional[pd.DataFrame] = None,
    balance_sheet: Optional[pd.DataFrame] = None,
    market_price: Optional[float] = None,
    currency: str = "INR",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate complete Multi-Year Historical Performance Detail and Trend Summary.

    Can be invoked in two flexible ways:
      1. By passing pre-computed `revenue_df`, `profitability_df`, `ratios_df`.
      2. By passing raw `income_stmt` and `balance_sheet` (engine computes prerequisites).

    Returns:
      (detail_df, summary_df)
    """
    # Auto-compute prerequisites if raw statements were provided
    if revenue_df is None and income_stmt is not None:
        revenue_df = analyze_revenue_earnings(income_stmt)
    if profitability_df is None and income_stmt is not None:
        profitability_df = analyze_profitability(income_stmt)
    if ratios_df is None and income_stmt is not None and balance_sheet is not None:
        ratios_df = analyze_financial_ratios(income_stmt, balance_sheet, market_price=market_price)

    # Collect all available periods
    period_set = set()
    for d in [revenue_df, profitability_df, ratios_df]:
        if d is not None and "Financial_Year" in d.columns:
            period_set.update(d["Financial_Year"].dropna().astype(str).tolist())

    periods = normalize_periods(period_set, descending=False)
    detail_rows: List[Dict[str, Any]] = []

    def _lookup(df: Optional[pd.DataFrame], period: str, col: str) -> Any:
        if df is None or df.empty or col not in df.columns:
            return np.nan
        match = df[df["Financial_Year"].astype(str) == str(period)]
        if match.empty:
            return np.nan
        val = match.iloc[0][col]
        return val if is_valid_number(val) else np.nan

    for p in periods:
        rev_raw = _lookup(revenue_df, p, "Revenue")
        ni_raw  = _lookup(revenue_df, p, "Net_Income")
        gp_raw  = _lookup(profitability_df, p, "Gross_Profit")
        op_raw  = _lookup(profitability_df, p, "Operating_Income")
        eb_raw  = _lookup(profitability_df, p, "EBITDA")

        # Scale monetary values (default Crore for INR, Million for USD)
        rev_scaled, _ = scale_currency_amount(rev_raw, currency=currency)
        ni_scaled, _  = scale_currency_amount(ni_raw, currency=currency)
        gp_scaled, _  = scale_currency_amount(gp_raw, currency=currency)
        op_scaled, _  = scale_currency_amount(op_raw, currency=currency)
        eb_scaled, _  = scale_currency_amount(eb_raw, currency=currency)

        detail_rows.append({
            "Financial_Year":         p,
            "Revenue_Cr":             rev_scaled,
            "Net_Income_Cr":          ni_scaled,
            "Revenue_Growth_%":       _lookup(revenue_df, p, "Revenue_Growth_%"),
            "NetIncome_Growth_%":     _lookup(revenue_df, p, "Earnings_Growth_%"),
            "Gross_Profit_Cr":        gp_scaled,
            "Operating_Income_Cr":    op_scaled,
            "EBITDA_Cr":              eb_scaled,
            "Gross_Profit_Margin_%":  _lookup(profitability_df, p, "Gross_Profit_Margin_%"),
            "Operating_Margin_%":     _lookup(profitability_df, p, "Operating_Margin_%"),
            "Net_Profit_Margin_%":    _lookup(profitability_df, p, "Net_Profit_Margin_%"),
            "EBITDA_Margin_%":        _lookup(profitability_df, p, "EBITDA_Margin_%"),
            "EPS":                    _lookup(ratios_df, p, "EPS"),
            "ROE_%":                  _lookup(ratios_df, p, "ROE_%"),
        })

    detail_df = pd.DataFrame(detail_rows)
    if detail_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Calculate YoY Absolute & Percentage Changes
    yoy_abs_map = {
        "Revenue_Cr":            "Revenue_YoY_Change_Cr",
        "Net_Income_Cr":         "NetIncome_YoY_Change_Cr",
        "Gross_Profit_Cr":       "GrossProfit_YoY_Change_Cr",
        "Operating_Income_Cr":   "OperatingIncome_YoY_Change_Cr",
        "EBITDA_Cr":             "EBITDA_YoY_Change_Cr",
        "EPS":                   "EPS_YoY_Change",
        "Gross_Profit_Margin_%": "GrossProfitMargin_YoY_Change_%pts",
        "Operating_Margin_%":    "OperatingMargin_YoY_Change_%pts",
        "Net_Profit_Margin_%":   "NetProfitMargin_YoY_Change_%pts",
        "EBITDA_Margin_%":       "EBITDAMargin_YoY_Change_%pts",
        "ROE_%":                 "ROE_YoY_Change_%pts",
    }
    for src, dst in yoy_abs_map.items():
        detail_df[dst] = np.nan
        for i in range(1, len(detail_df)):
            cur  = detail_df.loc[i,     src]
            prev = detail_df.loc[i - 1, src]
            detail_df.loc[i, dst] = safe_diff(cur, prev, decimals=4)

    yoy_pct_map = {
        "Revenue_Cr":          "Revenue_YoY_%",
        "Net_Income_Cr":       "NetIncome_YoY_%",
        "Gross_Profit_Cr":     "GrossProfit_YoY_%",
        "Operating_Income_Cr": "OperatingIncome_YoY_%",
        "EBITDA_Cr":           "EBITDA_YoY_%",
        "EPS":                 "EPS_YoY_%",
    }
    for src, dst in yoy_pct_map.items():
        detail_df[dst] = np.nan
        for i in range(1, len(detail_df)):
            cur  = detail_df.loc[i,     src]
            prev = detail_df.loc[i - 1, src]
            detail_df.loc[i, dst] = safe_pct_change(cur, prev, decimals=4)

    # -------------------------------------------------------------------
    # Summary Table Generation
    # -------------------------------------------------------------------
    tracked_metrics = [
        ("Revenue_Cr",            "INR Cr" if currency == "INR" else "M/B"),
        ("Net_Income_Cr",         "INR Cr" if currency == "INR" else "M/B"),
        ("Gross_Profit_Margin_%", "%"),
        ("Operating_Margin_%",    "%"),
        ("Net_Profit_Margin_%",   "%"),
        ("EBITDA_Margin_%",       "%"),
        ("EPS",                   currency),
        ("ROE_%",                 "%"),
    ]

    summary_rows: List[Dict[str, Any]] = []
    for col, unit in tracked_metrics:
        valid_mask = detail_df[col].notna()
        valid_vals = detail_df.loc[valid_mask, col].tolist()
        valid_yrs  = detail_df.loc[valid_mask, "Financial_Year"].tolist()

        first_v = valid_vals[0]  if valid_vals else np.nan
        last_v  = valid_vals[-1] if valid_vals else np.nan
        first_y = valid_yrs[0]   if valid_yrs  else "N/A"
        last_y  = valid_yrs[-1]  if valid_yrs  else "N/A"

        chg_abs = safe_diff(last_v, first_v, decimals=4)
        chg_pct = safe_pct_change(last_v, first_v, decimals=4)
        trend   = trend_direction(valid_vals)

        summary_rows.append({
            "Metric":               col,
            "Unit":                 unit,
            "First_Year":           first_y,
            "First_Value":          first_v,
            "Last_Year":            last_y,
            "Last_Value":           last_v,
            "Years_With_Data":      len(valid_vals),
            "Absolute_Change":      chg_abs,
            "Percentage_Change_%":  chg_pct,
            "Overall_Trend":        trend,
        })

    summary_df = pd.DataFrame(summary_rows)
    return detail_df, summary_df


# ===========================================================================
# FEATURE 7: FINANCIAL DATA QUALITY & VALIDATION
# ===========================================================================

def audit_financial_data_quality(
    income_stmt: pd.DataFrame,
    balance_sheet: Optional[pd.DataFrame] = None,
    derived_data: Optional[Dict[str, pd.DataFrame]] = None,
    ticker: str = "UNKNOWN",
) -> Dict[str, Any]:
    """
    Perform comprehensive data quality audit and validation on financial statements.

    Checks:
      1. Missing Statements / Line Items / Periods.
      2. Period alignment between Income Statement and Balance Sheet.
      3. Unusual negative numbers (negative revenue, negative total assets vs valid net losses).
      4. Invalid calculations and denominator division-by-zero risks (zero equity, zero liabilities).
      5. Cross-analysis consistency across derived analytical tables.

    Returns:
      Dict with:
        - "issues": List of structured issue dictionaries
        - "severity_counts": {"CRITICAL": int, "WARNING": int, "INFO": int}
        - "overall_status": "PASS" | "WARNING" | "CRITICAL"
        - "coverage": Per-statement coverage and period statistics
    """
    issues: List[Dict[str, Any]] = []

    def _log(cat: str, sev: str, src: str, metric: str, period: str, desc: str, impact: str):
        issues.append({
            "Ticker": ticker,
            "Category": cat,          # Missing Data, Inconsistent Data, Invalid Calculation
            "Severity": sev,          # CRITICAL, WARNING, INFO
            "Source_File": src,
            "Metric": metric,
            "Period": str(period),
            "Description": desc,
            "Impact": impact,
        })

    # 1. Income Statement Checks
    inc_periods = _extract_statement_periods(income_stmt)
    if not inc_periods:
        _log(
            "Missing Data", "CRITICAL", "Income_Statement", "All_Metrics", "All",
            "Income statement is empty or contains no parseable financial periods",
            "Cannot perform revenue, earnings, or profitability analysis",
        )
    else:
        for p in inc_periods:
            rev = get_metric(income_stmt, ["Total Revenue", "Operating Revenue"], period=p)
            ni  = get_metric(income_stmt, ["Net Income", "Normalized Income"], period=p)

            # Check for empty or sparse periods
            if isinstance(income_stmt, pd.DataFrame) and p in income_stmt.columns:
                non_nulls = int(income_stmt[p].dropna().count())
                total_rows = len(income_stmt)
                if non_nulls <= 2:
                    non_null_rows = ", ".join(income_stmt[p].dropna().index.tolist())
                    _log(
                        "Missing Data", "CRITICAL", "Income_Statement", "Core_Metrics", p,
                        f"Financial period {p} only has {non_nulls}/{total_rows} metrics ({non_null_rows})",
                        "Missing Total Revenue, Net Income, Gross Profit; unusable for performance analysis",
                    )
                elif rev is None or ni is None:
                    _log(
                        "Missing Data", "WARNING", "Income_Statement", "Revenue_or_NetIncome", p,
                        f"Period {p} is missing Total Revenue or Net Income",
                        "Margins and growth cannot be fully computed for this period",
                    )
            elif rev is None or ni is None:
                _log(
                    "Missing Data", "WARNING", "Income_Statement", "Revenue_or_NetIncome", p,
                    f"Period {p} is missing Total Revenue or Net Income",
                    "Margins and growth cannot be fully computed for this period",
                )

            # Check unusual signs
            if rev is not None and rev < 0:
                _log(
                    "Inconsistent Data", "CRITICAL", "Income_Statement", "Revenue", p,
                    f"Negative revenue detected ({rev}) in period {p}",
                    "Revenues must be non-negative; check data source",
                )
            if ni is not None and ni < 0:
                _log(
                    "Inconsistent Data", "INFO", "Income_Statement", "Net_Income", p,
                    f"Negative net income (loss) detected ({ni}) in period {p}",
                    "Legitimate accounting loss; correctly preserved without error flagging",
                )

    # 2. Balance Sheet Checks & Cross-Period Alignment
    bs_periods: List[str] = []
    if balance_sheet is not None and not balance_sheet.empty:
        bs_periods = _extract_statement_periods(balance_sheet)

        for p in bs_periods:
            ta = get_metric(balance_sheet, ["Total Assets"], period=p)
            eq = get_metric(balance_sheet, ["Stockholders Equity"], period=p)
            cl = get_metric(balance_sheet, ["Current Liabilities"], period=p)
            td = get_metric(balance_sheet, ["Total Debt"], period=p)

            # Sign checks
            if ta is not None and ta < 0:
                _log(
                    "Inconsistent Data", "CRITICAL", "Balance_Sheet", "Total_Assets", p,
                    f"Negative total assets detected ({ta}) in period {p}",
                    "Assets cannot be negative",
                )
            if td is not None and td < 0:
                _log(
                    "Inconsistent Data", "WARNING", "Balance_Sheet", "Total_Debt", p,
                    f"Negative total debt detected ({td}) in period {p}",
                    "Verify whether net cash was mistakenly recorded as negative gross debt",
                )

            # Zero denominator checks
            if eq is not None and eq == 0:
                _log(
                    "Invalid Calculation", "CRITICAL", "Balance_Sheet", "Stockholders_Equity", p,
                    f"Stockholders Equity is 0 in period {p}, resulting in division by zero for leverage & ROE",
                    "Cannot compute Debt-to-Equity or ROE",
                )
            if cl is not None and cl == 0:
                _log(
                    "Invalid Calculation", "CRITICAL", "Balance_Sheet", "Current_Liabilities", p,
                    f"Current Liabilities is 0 in period {p}, resulting in division by zero for Current Ratio",
                    "Cannot compute Current Ratio",
                )
            if td is not None and td == 0:
                _log(
                    "Invalid Calculation", "WARNING", "Balance_Sheet", "Total_Debt", p,
                    f"Total Debt is 0 in period {p}, resulting in division by zero for Cash-to-Debt",
                    "Zero-debt company requires alternative liquidity measures",
                )

        # Cross-Statement Period Alignment
        inc_only = set(inc_periods) - set(bs_periods)
        bs_only  = set(bs_periods) - set(inc_periods)

        for p in normalize_periods(inc_only):
            _log(
                "Missing Data", "WARNING", "Balance_Sheet", "Balance_Sheet_Period", p,
                f"Period {p} exists in Income Statement but is missing from Balance Sheet",
                "Combined ratios (e.g. ROE = Net Income / Equity, Asset Turnover) cannot be calculated for this period",
            )
        for p in normalize_periods(bs_only):
            _log(
                "Missing Data", "WARNING", "Income_Statement", "Income_Statement_Period", p,
                f"Period {p} exists in Balance Sheet but is missing from Income Statement",
                "Cannot compute profitability ratios for this period",
            )

    # 3. Derived Analytical Tables Consistency (if passed)
    if derived_data:
        prof_df  = derived_data.get("profitability")
        rat_df   = derived_data.get("financial_ratios")

        if prof_df is not None and not prof_df.empty:
            for _, r in prof_df.iterrows():
                fy = str(r.get("Financial_Year"))
                if pd.isna(r.get("Revenue")) and pd.isna(r.get("Net_Profit_Margin_%")):
                    _log(
                        "Invalid Calculation", "INFO", "Profitability_Analysis", "Margins", fy,
                        f"Margins could not be calculated for {fy} because Revenue is missing (NaN)",
                        "Preserved as NaN without silent zero-substitution",
                    )

        if rat_df is not None and not rat_df.empty and "PE_Ratio" in rat_df.columns:
            missing_pe_years = rat_df.loc[rat_df["PE_Ratio"].isna(), "Financial_Year"].dropna().astype(str).tolist()
            if missing_pe_years:
                _log(
                    "Missing Data", "INFO", "Financial_Ratios_Analysis", "PE_Ratio & PB_Ratio",
                    "; ".join(missing_pe_years),
                    f"P/E and P/B ratios are NaN for historical years ({', '.join(missing_pe_years)}) because market data fetcher only provides current spot price",
                    "Expected limitation: historical point-in-time P/E and P/B are not backfilled with current stock price to avoid lookahead bias",
                )

    # Severity Counts & Overall Status
    sev_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for iss in issues:
        s = iss["Severity"]
        if s in sev_counts:
            sev_counts[s] += 1

    if sev_counts["CRITICAL"] > 0:
        overall_status = "CRITICAL"
    elif sev_counts["WARNING"] > 0:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return {
        "ticker": ticker,
        "overall_status": overall_status,
        "severity_counts": sev_counts,
        "issues": issues,
        "income_periods": inc_periods,
        "balance_sheet_periods": bs_periods,
    }


# ===========================================================================
# FEATURE 8: RULE-BASED PROFITABILITY CLASSIFICATION
# ===========================================================================

DEFAULT_PROFITABILITY_THRESHOLDS = {
    "highly_profitable_min": 15.0,      # Net Margin >= 15.0%
    "moderately_profitable_min": 5.0,   # Net Margin >= 5.0% and < 15.0%
    "low_profitable_min": 0.0,          # Net Margin > 0.0% and < 5.0%
    # Net Margin <= 0.0% -> "Not Profitable"
    # Net Margin is missing/NaN -> "Insufficient Data"
}

PROFITABILITY_RULE_DISCLAIMER = (
    "NOTE: These classification thresholds are analytical heuristics defined for "
    "the StockIntel Financial Agent. They are NOT official accounting standards, "
    "statutory definitions, or investment advice."
)


def classify_profitability_margin(
    net_margin: Optional[float],
    thresholds: Optional[Dict[str, float]] = None,
) -> Tuple[str, str]:
    """
    Classify a single Net Profit Margin percentage using configurable thresholds.

    Returns:
        (classification_tier, rationale_string)
    """
    th = thresholds or DEFAULT_PROFITABILITY_THRESHOLDS

    if net_margin is None or not is_valid_number(net_margin):
        return "Insufficient Data", "Net Profit Margin is missing or cannot be calculated"

    val = float(net_margin)
    hp_min = th["highly_profitable_min"]
    mp_min = th["moderately_profitable_min"]
    lp_min = th["low_profitable_min"]

    if val >= hp_min:
        return "Highly Profitable", f"Net Profit Margin ({val:.2f}%) >= {hp_min}%"
    elif val >= mp_min:
        return "Moderately Profitable", f"Net Profit Margin ({val:.2f}%) between {mp_min}% and {hp_min}%"
    elif val > lp_min:
        return "Low Profitable", f"Net Profit Margin ({val:.2f}%) between {lp_min}% and {mp_min}%"
    else:
        return "Not Profitable", f"Net Profit Margin ({val:.2f}%) <= {lp_min}% (operating at a net loss or breakeven)"


def classify_profitability(
    profitability_df: Optional[pd.DataFrame] = None,
    income_stmt: Optional[pd.DataFrame] = None,
    data_quality_issues: Optional[List[Dict[str, Any]]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    ticker: str = "UNKNOWN",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform complete rule-based profitability tier classification across available years.

    Can be invoked with:
      - `profitability_df` pre-computed, OR
      - `income_stmt` (calls `analyze_profitability()` internally).

    Returns:
      (detail_df, summary_df)
    """
    th = thresholds or DEFAULT_PROFITABILITY_THRESHOLDS

    if profitability_df is None and income_stmt is not None:
        profitability_df = analyze_profitability(income_stmt)

    if profitability_df is None or profitability_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    prof = profitability_df.sort_values("Financial_Year").reset_index(drop=True)

    # Map data quality warnings by period
    dq_by_period: Dict[str, List[str]] = {}
    if data_quality_issues:
        for iss in data_quality_issues:
            p_str = str(iss.get("Period", ""))
            sev = iss.get("Severity", "")
            cat = iss.get("Category", "")
            desc = iss.get("Description", "")
            note = f"[{sev}] {cat}: {desc}"
            for sp in p_str.split(";"):
                sp_clean = sp.strip()
                if sp_clean:
                    dq_by_period.setdefault(sp_clean, []).append(note)

    detail_rows: List[Dict[str, Any]] = []
    margin_series: List[Optional[float]] = []

    for _, r in prof.iterrows():
        fy   = str(r["Financial_Year"])
        npm  = r.get("Net_Profit_Margin_%")
        gpm  = r.get("Gross_Profit_Margin_%")
        opm  = r.get("Operating_Margin_%")
        ebm  = r.get("EBITDA_Margin_%")
        rg   = r.get("Revenue_Growth_%")
        nig  = r.get("NetIncome_Growth_%")
        roe  = r.get("ROE_%")

        cls_label, rationale = classify_profitability_margin(npm, thresholds=th)
        margin_series.append(npm if is_valid_number(npm) else None)

        p_warnings = dq_by_period.get(fy, [])
        warning_text = "; ".join(p_warnings) if p_warnings else "None"

        detail_rows.append({
            "Ticker":                     ticker,
            "Financial_Year":             fy,
            "Net_Profit_Margin_%":        round(npm, 4) if is_valid_number(npm) else np.nan,
            "Classification":             cls_label,
            "Classification_Rationale":   rationale,
            "Gross_Profit_Margin_%":      round(gpm, 4) if is_valid_number(gpm) else np.nan,
            "Operating_Margin_%":         round(opm, 4) if is_valid_number(opm) else np.nan,
            "EBITDA_Margin_%":            round(ebm, 4) if is_valid_number(ebm) else np.nan,
            "Revenue_Growth_%":           round(rg, 4)  if is_valid_number(rg)  else np.nan,
            "Net_Income_Growth_%":        round(nig, 4) if is_valid_number(nig) else np.nan,
            "ROE_%":                      round(roe, 4) if is_valid_number(roe) else np.nan,
            "Data_Quality_Warning":       warning_text,
        })

    detail_df = pd.DataFrame(detail_rows)

    # -------------------------------------------------------------------
    # Latest Period Summary
    # -------------------------------------------------------------------
    valid_rows = detail_df[detail_df["Net_Profit_Margin_%"].notna()]
    latest_row = valid_rows.iloc[-1] if not valid_rows.empty else detail_df.iloc[-1]

    latest_fy    = latest_row["Financial_Year"]
    latest_class = latest_row["Classification"]
    latest_npm   = latest_row["Net_Profit_Margin_%"]
    latest_rat   = latest_row["Classification_Rationale"]

    # Trend calculation
    trend = trend_direction([m for m in margin_series if m is not None])

    has_critical_in_latest = "CRITICAL" in str(latest_row["Data_Quality_Warning"])
    quality_status = (
        "Caution: Critical data quality issues detected in latest period"
        if has_critical_in_latest
        else "Reliable: No critical data quality issues affect the latest evaluated period"
    )

    summary_data = [
        {"Item": "Company Ticker",                       "Value": ticker},
        {"Item": "Primary Evaluation Metric",            "Value": "Net Profit Margin (%)"},
        {"Item": "Latest Evaluated Financial Year",      "Value": str(latest_fy)},
        {"Item": "Latest Net Profit Margin (%)",          "Value": f"{latest_npm:.2f}%" if is_valid_number(latest_npm) else "N/A"},
        {"Item": "Overall Profitability Class",          "Value": latest_class},
        {"Item": "Classification Rationale",             "Value": latest_rat},
        {"Item": "Multi-Year Margin Trend",              "Value": trend},
        {"Item": "Gross Profit Margin (%)",              "Value": f"{latest_row['Gross_Profit_Margin_%']:.2f}%" if is_valid_number(latest_row['Gross_Profit_Margin_%']) else "N/A"},
        {"Item": "Operating Profit Margin (%)",          "Value": f"{latest_row['Operating_Margin_%']:.2f}%" if is_valid_number(latest_row['Operating_Margin_%']) else "N/A"},
        {"Item": "EBITDA Margin (%)",                    "Value": f"{latest_row['EBITDA_Margin_%']:.2f}%" if is_valid_number(latest_row['EBITDA_Margin_%']) else "N/A"},
        {"Item": "Data Quality Status",                  "Value": quality_status},
        {"Item": "Data Quality Warning for Latest Period", "Value": str(latest_row["Data_Quality_Warning"])},
        {"Item": "Configured Threshold - Highly Profitable", "Value": f">= {th['highly_profitable_min']}%"},
        {"Item": "Configured Threshold - Moderately Profitable", "Value": f">= {th['moderately_profitable_min']}% and < {th['highly_profitable_min']}%"},
        {"Item": "Configured Threshold - Low Profitable", "Value": f"> {th['low_profitable_min']}% and < {th['moderately_profitable_min']}%"},
        {"Item": "Configured Threshold - Not Profitable", "Value": f"<= {th['low_profitable_min']}%"},
        {"Item": "Rule Disclaimer",                      "Value": PROFITABILITY_RULE_DISCLAIMER},
    ]
    summary_df = pd.DataFrame(summary_data)

    return detail_df, summary_df


# ===========================================================================
# FEATURE 6: REUSABLE PEER COMPARISON
# ===========================================================================

# Standard metrics supported in peer comparison
PEER_COMPARISON_METRICS = [
    ("Revenue_Cr",             "monetary",   "Higher"),
    ("Revenue_Growth_%",       "percentage", "Higher"),
    ("Net_Income_Cr",          "monetary",   "Higher"),
    ("Net_Income_Growth_%",    "percentage", "Higher"),
    ("Gross_Profit_Margin_%",  "percentage", "Higher"),
    ("Operating_Margin_%",     "percentage", "Higher"),
    ("Net_Profit_Margin_%",    "percentage", "Higher"),
    ("EBITDA_Margin_%",        "percentage", "Higher"),
    ("ROE_%",                  "percentage", "Higher"),
    ("Debt_to_Equity",         "ratio",      "Lower"),
    ("Debt_to_Assets",         "ratio",      "Lower"),
    ("Current_Ratio",          "ratio",      "Higher"),
    ("EPS",                    "monetary",   "Higher"),
    ("PE_Ratio",               "ratio",      "Contextual"),
    ("PB_Ratio",               "ratio",      "Contextual"),
]

PEER_COMPARISON_DISCLAIMER = (
    "NOTE: Peer comparisons are based on publicly reported annual filings. "
    "Conglomerates, multi-sector operators, and companies with different business models "
    "or capital structures may not be directly comparable across all metrics. "
    "Cross-currency monetary amounts are never compared directly without explicit foreign exchange rates."
)


def _normalize_company_peer_record(
    comp: Union[Dict[str, Any], pd.Series],
    is_target: bool = False,
    target_currency: str = "INR",
) -> Dict[str, Any]:
    """
    Standardize a company's financial record for peer comparison.
    Extracts core identification, metadata, and the 15 standard comparison metrics.
    """
    data = comp.to_dict() if isinstance(comp, pd.Series) else dict(comp)

    ticker = str(data.get("Ticker") or data.get("ticker") or "UNKNOWN").strip().upper()
    name   = str(data.get("Company_Name") or data.get("company_name") or data.get("name") or ticker)
    curr   = str(data.get("Currency") or data.get("currency") or target_currency).strip().upper()
    period = str(data.get("FY_Period") or data.get("fy_period") or data.get("period") or "Latest")
    sector = data.get("Sector") or data.get("sector")
    industry = data.get("Industry") or data.get("industry")
    rationale = data.get("Peer_Rationale") or data.get("peer_rationale") or data.get("rationale") or ("Target company" if is_target else "Peer company")
    notes = data.get("Data_Notes") or data.get("data_notes") or "OK"

    # Extract 15 standard metrics with flexible aliases
    def _extract(metric_key: str) -> Optional[float]:
        # Direct hit
        if metric_key in data and is_valid_number(data[metric_key]):
            return float(data[metric_key])

        # Aliases
        alias_map = {
            "Revenue_Cr":          ["Revenue_Cr", "revenue_cr", "Revenue", "revenue"],
            "Revenue_Growth_%":    ["Revenue_Growth_%", "revenue_growth_pct", "revenue_growth"],
            "Net_Income_Cr":       ["Net_Income_Cr", "net_income_cr", "Net_Income", "net_income"],
            "Net_Income_Growth_%": ["Net_Income_Growth_%", "net_income_growth_pct", "Earnings_Growth_%"],
            "Gross_Profit_Margin_%": ["Gross_Profit_Margin_%", "gross_profit_margin_pct", "gross_margin"],
            "Operating_Margin_%":  ["Operating_Margin_%", "operating_margin_pct", "operating_margin"],
            "Net_Profit_Margin_%": ["Net_Profit_Margin_%", "net_profit_margin_pct", "net_margin"],
            "EBITDA_Margin_%":     ["EBITDA_Margin_%", "ebitda_margin_pct", "ebitda_margin"],
            "ROE_%":               ["ROE_%", "roe_pct", "roe", "ROE"],
            "Debt_to_Equity":      ["Debt_to_Equity", "debt_to_equity", "Debt_to_Equity_Ratio"],
            "Debt_to_Assets":      ["Debt_to_Assets", "debt_to_assets", "Debt_to_Assets_Ratio"],
            "Current_Ratio":       ["Current_Ratio", "current_ratio"],
            "EPS":                 ["EPS", "eps", "EPS_Diluted"],
            "PE_Ratio":            ["PE_Ratio", "pe_ratio", "pe"],
            "PB_Ratio":            ["PB_Ratio", "pb_ratio", "pb"],
        }
        for alias in alias_map.get(metric_key, []):
            if alias in data and is_valid_number(data[alias]):
                val = float(data[alias])
                # Scale raw unscaled revenue/net income if needed
                if "_Cr" in metric_key and abs(val) > 1e7:
                    scaled, _ = scale_currency_amount(val, currency=curr)
                    return scaled
                return val
        return None

    metrics_dict: Dict[str, Optional[float]] = {}
    for m_key, _, _ in PEER_COMPARISON_METRICS:
        val = _extract(m_key)
        metrics_dict[m_key] = round(val, 4) if val is not None else None

    return {
        "ticker":         ticker,
        "company_name":   name,
        "is_target":      is_target,
        "currency":       curr,
        "fy_period":      period,
        "sector":         str(sector) if sector else None,
        "industry":       str(industry) if industry else None,
        "peer_rationale": str(rationale),
        "data_notes":     str(notes),
        "metrics":        metrics_dict,
    }


def compare_peers(
    target_company: Union[Dict[str, Any], pd.Series],
    peer_companies: Union[List[Union[Dict[str, Any], pd.Series]], pd.DataFrame],
    target_ticker: Optional[str] = None,
    metadata: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Perform reusable in-memory Peer Comparison between a target company and a list of peers.

    Args:
      target_company: Dictionary or Series with target's financial metrics.
      peer_companies: List of dictionaries or DataFrame representing peer companies.
      target_ticker:  Optional explicit ticker identifier for the target.
      metadata:       Optional dict {ticker: {"sector": ..., "industry": ..., "rationale": ...}}

    Features:
      - Validates and standardizes 15 core financial metrics.
      - Never invents missing data; preserves None for unavailable values.
      - Detects currency mismatches: excludes cross-currency comparisons from monetary averages.
      - Detects sector/industry mismatches and issues contextual warnings.
      - Computes peer benchmark statistics (peer mean, median, min, max, target rank) when comparable data exists.
      - Output is a JSON-serializable dictionary suitable for API and UI rendering.
    """
    warnings: List[str] = []

    # 1. Normalize target record
    target_rec = _normalize_company_peer_record(target_company, is_target=True)
    if target_ticker:
        target_rec["ticker"] = target_ticker.strip().upper()

    target_curr   = target_rec["currency"]
    target_sector = target_rec["sector"]

    # 2. Normalize peer records
    peers_list: List[Dict[str, Any]] = []
    if isinstance(peer_companies, pd.DataFrame):
        for _, row in peer_companies.iterrows():
            rec = _normalize_company_peer_record(row, is_target=False, target_currency=target_curr)
            if rec["ticker"] != target_rec["ticker"]:
                peers_list.append(rec)
    elif isinstance(peer_companies, (list, tuple)):
        for item in peer_companies:
            rec = _normalize_company_peer_record(item, is_target=False, target_currency=target_curr)
            if rec["ticker"] != target_rec["ticker"]:
                peers_list.append(rec)

    # Apply external metadata if provided
    all_companies = [target_rec] + peers_list
    if metadata:
        for c in all_companies:
            t = c["ticker"]
            if t in metadata:
                m = metadata[t]
                if m.get("sector"): c["sector"] = m["sector"]
                if m.get("industry"): c["industry"] = m["industry"]
                if m.get("rationale"): c["peer_rationale"] = m["rationale"]

    # 3. Currency and Sector Compatibility Audits
    for peer in peers_list:
        p_curr = peer["currency"]
        p_tick = peer["ticker"]
        p_sec  = peer["sector"]

        if p_curr != target_curr:
            warnings.append(
                f"Currency Mismatch: Peer '{p_tick}' reports in {p_curr} while Target reports in {target_curr}. "
                "Monetary metrics (Revenue, Net Income, EPS) cannot be compared directly and are excluded from group monetary averages."
            )

        if target_sector and p_sec and p_sec.lower() != target_sector.lower():
            warnings.append(
                f"Cross-Sector Peer: Peer '{p_tick}' operates in sector '{p_sec}' while Target operates in '{target_sector}'. "
                "Capital structures and margin baselines differ significantly; interpret comparison with caution."
            )

    if not peers_list:
        warnings.append("No peer companies were provided for comparison.")

    # 4. Benchmark Statistics & Ranking Calculation
    benchmarks: Dict[str, Any] = {}

    for metric_key, metric_type, direction in PEER_COMPARISON_METRICS:
        target_val = target_rec["metrics"].get(metric_key)

        # Filter valid peer values
        valid_peer_vals: List[float] = []
        for peer in peers_list:
            # For monetary values, only include peers with matching currency
            if metric_type == "monetary" and peer["currency"] != target_curr:
                continue
            val = peer["metrics"].get(metric_key)
            if val is not None and is_valid_number(val):
                valid_peer_vals.append(float(val))

        # Check if enough peer data exists
        if not valid_peer_vals:
            benchmarks[metric_key] = {
                "target_value": target_val,
                "peer_average": None,
                "peer_median":  None,
                "peer_min":     None,
                "peer_max":     None,
                "peer_count":   0,
                "target_rank":  None,
                "total_ranked": 0,
                "unit_note":    "Incomparable / Insufficient peer data",
            }
            continue

        peer_avg = round(float(np.mean(valid_peer_vals)), 4)
        peer_med = round(float(np.median(valid_peer_vals)), 4)
        peer_min = round(float(np.min(valid_peer_vals)), 4)
        peer_max = round(float(np.max(valid_peer_vals)), 4)

        # Target Rank (1 = best)
        target_rank = None
        total_ranked = len(valid_peer_vals)
        if target_val is not None and is_valid_number(target_val):
            total_ranked += 1
            combined = valid_peer_vals + [float(target_val)]
            if direction == "Higher":
                # Highest is rank 1
                combined_sorted = sorted(combined, reverse=True)
            elif direction == "Lower":
                # Lowest is rank 1 (e.g. debt-to-equity)
                combined_sorted = sorted(combined, reverse=False)
            else:
                combined_sorted = sorted(combined, reverse=True)

            target_rank = combined_sorted.index(float(target_val)) + 1

        benchmarks[metric_key] = {
            "target_value": target_val,
            "peer_average": peer_avg,
            "peer_median":  peer_med,
            "peer_min":     peer_min,
            "peer_max":     peer_max,
            "peer_count":   len(valid_peer_vals),
            "target_rank":  target_rank,
            "total_ranked": total_ranked if target_rank is not None else len(valid_peer_vals),
            "unit_note":    target_curr if metric_type == "monetary" else ("%" if metric_type == "percentage" else "ratio"),
        }

    # 5. Build Flat Display Rows for tabular presentation
    tabular_records: List[Dict[str, Any]] = []
    for c in all_companies:
        rec = {
            "Ticker":         c["ticker"],
            "Company_Name":   c["company_name"],
            "Is_Target":      c["is_target"],
            "Currency":       c["currency"],
            "FY_Period":      c["fy_period"],
            "Sector":         c["sector"],
            "Peer_Rationale": c["peer_rationale"],
            "Data_Notes":     c["data_notes"],
        }
        rec.update(c["metrics"])
        tabular_records.append(rec)

    return {
        "target_ticker":       target_rec["ticker"],
        "target_company_name": target_rec["company_name"],
        "target_currency":     target_curr,
        "companies_compared":  len(all_companies),
        "peer_count":          len(peers_list),
        "companies":           all_companies,
        "comparison_table":    tabular_records,
        "peer_benchmarks":     benchmarks,
        "warnings":            warnings,
        "disclaimer":          PEER_COMPARISON_DISCLAIMER,
    }


# ===========================================================================
# MASTER CONVENIENCE RUNNER (UPDATED WITH FEATURES 6, 7 & 8)
# ===========================================================================

def run_fundamental_analysis(
    income_stmt: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    market_price: Optional[float] = None,
    price_date: Optional[str] = None,
    currency: str = "INR",
    ticker: str = "UNKNOWN",
    thresholds: Optional[Dict[str, float]] = None,
    peer_companies: Optional[Union[List[Dict[str, Any]], pd.DataFrame]] = None,
    peer_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run Features 1 through 5, Feature 6 (Peer Comparison, if provided),
    Feature 7 (Data Quality), and Feature 8 (Profitability Classification)
    purely in-memory and return a clean structured dictionary.
    """
    # Features 1-4
    rev_df  = analyze_revenue_earnings(income_stmt)
    prof_df = analyze_profitability(income_stmt)
    debt_df = analyze_debt_stability(balance_sheet)
    rat_df  = analyze_financial_ratios(
        income_stmt,
        balance_sheet,
        market_price=market_price,
        price_date=price_date
    )

    # Feature 5: Historical Performance
    hist_detail, hist_summary = compare_historical_performance(
        revenue_df=rev_df,
        profitability_df=prof_df,
        ratios_df=rat_df,
        currency=currency,
    )

    # Feature 7: Data Quality & Validation
    dq_result = audit_financial_data_quality(
        income_stmt=income_stmt,
        balance_sheet=balance_sheet,
        derived_data={"profitability": prof_df, "financial_ratios": rat_df},
        ticker=ticker,
    )

    # Feature 8: Rule-Based Profitability Classification
    prof_class_detail, prof_class_summary = classify_profitability(
        profitability_df=prof_df,
        data_quality_issues=dq_result.get("issues", []),
        thresholds=thresholds,
        ticker=ticker,
    )

    # Feature 6: Peer Comparison (Optional integration)
    peer_result = None
    if peer_companies is not None:
        # Build target company summary from latest valid figures
        latest_rev = rev_df.iloc[-1].to_dict() if not rev_df.empty else {}
        latest_prof = prof_df.iloc[-1].to_dict() if not prof_df.empty else {}
        latest_debt = debt_df.iloc[-1].to_dict() if not debt_df.empty else {}
        latest_rat = rat_df.iloc[-1].to_dict() if not rat_df.empty else {}

        target_summary_data = {
            "Ticker":                 ticker,
            "Currency":               currency,
            "FY_Period":              latest_rev.get("Financial_Year", "Latest"),
            "Revenue":                latest_rev.get("Revenue"),
            "Revenue_Growth_%":       latest_rev.get("Revenue_Growth_%"),
            "Net_Income":             latest_rev.get("Net_Income"),
            "Net_Income_Growth_%":    latest_rev.get("Earnings_Growth_%"),
            "Gross_Profit_Margin_%":  latest_prof.get("Gross_Profit_Margin_%"),
            "Operating_Margin_%":     latest_prof.get("Operating_Margin_%"),
            "Net_Profit_Margin_%":    latest_prof.get("Net_Profit_Margin_%"),
            "EBITDA_Margin_%":        latest_prof.get("EBITDA_Margin_%"),
            "Debt_to_Equity":         latest_debt.get("Debt_to_Equity_Ratio"),
            "Debt_to_Assets":         latest_debt.get("Debt_to_Assets_Ratio"),
            "Current_Ratio":          latest_debt.get("Current_Ratio"),
            "ROE_%":                  latest_rat.get("ROE_%"),
            "EPS":                    latest_rat.get("EPS"),
            "PE_Ratio":               latest_rat.get("PE_Ratio"),
            "PB_Ratio":               latest_rat.get("PB_Ratio"),
        }

        peer_result = compare_peers(
            target_company=target_summary_data,
            peer_companies=peer_companies,
            target_ticker=ticker,
            metadata=peer_metadata,
        )

    return {
        "ticker":                        ticker,
        "currency":                      currency,
        "revenue_earnings":              rev_df.to_dict(orient="records"),
        "profitability":                 prof_df.to_dict(orient="records"),
        "debt_stability":                debt_df.to_dict(orient="records"),
        "financial_ratios":              rat_df.to_dict(orient="records"),
        "historical_detail":             hist_detail.to_dict(orient="records"),
        "historical_summary":            hist_summary.to_dict(orient="records"),
        "data_quality":                  dq_result,
        "profitability_classification": {
            "detail":  prof_class_detail.to_dict(orient="records"),
            "summary": prof_class_summary.to_dict(orient="records"),
        },
        "peer_comparison":               peer_result,
    }
