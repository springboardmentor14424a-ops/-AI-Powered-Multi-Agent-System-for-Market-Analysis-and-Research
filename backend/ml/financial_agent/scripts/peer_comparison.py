"""
peer_comparison.py
-------------------
Module 3 – Financial Agent | Feature 6: Peer Comparison

Reusable module that fetches and compares key financial metrics across
a primary company and a list of peer companies.

Design principles:
  - Fully reusable: accepts any ticker + peer list (not Reliance-specific).
  - Separates data retrieval, calculation, and comparison logic.
  - Never invents missing data or silently substitutes zero for NaN.
  - Handles yfinance errors, unsupported tickers and incomplete statements.
  - Labels each metric's reporting period (most recent annual FY).
  - Documents peer selection rationale and comparability limitations.

Metrics compared:
  Revenue, Revenue Growth %, Net Income, Net Income Growth %,
  Gross Profit Margin %, Operating Margin %, Net Profit Margin %,
  EBITDA Margin %, ROE %, Debt-to-Equity, Debt-to-Assets,
  Current Ratio, EPS (Diluted), P/E Ratio, P/B Ratio

Usage (from project root):
  python backend/ml/financial_agent/scripts/peer_comparison.py

Outputs (in backend/ml/financial_agent/data/processed/):
  peer_comparison_metrics.csv      – raw per-company metrics
  reliance_peer_comparison.csv     – ranked/formatted comparison table

Do NOT modify this file when running for other companies.
Instead import and call compare_peers() with different arguments.
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path setup – consistent with existing project scripts
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR     = Path(__file__).resolve().parents[1] / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_METRICS    = DATA_DIR / "peer_comparison_metrics.csv"
OUTPUT_COMPARISON = DATA_DIR / "reliance_peer_comparison.csv"

CR = 1e7   # 1 Crore = 10,000,000 INR


# ===========================================================================
# PEER GROUP DEFINITION
# ===========================================================================
#
# Primary company: Reliance Industries (RELIANCE.NS)
#
# Peer selection rationale:
#   Reliance is a highly diversified Indian conglomerate spanning:
#   Oil & gas, Petrochemicals, Retail (Reliance Retail), Telecom (Jio),
#   Media, and new energy.
#
#   Because no single Indian listed company mirrors this exact diversification,
#   peers are chosen by SEGMENT relevance and large-cap comparability:
#
#   1. ONGC.NS       — Oil & Natural Gas Corp: core O&G overlap
#   2. IOC.NS        — Indian Oil Corp: downstream O&G + refining overlap
#   3. BPCL.NS       — Bharat Petroleum: refining + fuel retail overlap
#   4. TCS.NS        — Tata Consultancy Services: large-cap benchmark
#                      (included for size/market-cap comparison only)
#   5. HINDUNILVR.NS — Hindustan Unilever: consumer/retail segment proxy
#   6. BHARTIARTL.NS — Bharti Airtel: telecom (Jio) segment proxy
#
#   LIMITATION: No peer is fully comparable to Reliance across all segments.
#   Margin and ratio comparisons must be interpreted with this in mind.
#   Sector-specific peers (O&G, Telecom, Retail) are individually more
#   comparable than the group as a whole.
#
# ===========================================================================

DEFAULT_PRIMARY = "RELIANCE.NS"
DEFAULT_PEERS = [
    "ONGC.NS",
    "IOC.NS",
    "BPCL.NS",
    "TCS.NS",
    "HINDUNILVR.NS",
    "BHARTIARTL.NS",
]

PEER_RATIONALE = {
    "ONGC.NS":       "O&G segment comparable (upstream)",
    "IOC.NS":        "O&G + refining segment comparable (downstream)",
    "BPCL.NS":       "Refining + fuel retail comparable",
    "TCS.NS":        "Large-cap benchmark (size comparison only)",
    "HINDUNILVR.NS": "Consumer/retail segment proxy",
    "BHARTIARTL.NS": "Telecom segment proxy (vs Jio)",
}


# ===========================================================================
# SECTION 1: DATA RETRIEVAL
# ===========================================================================

def safe_get(d: dict, *keys, default=np.nan):
    """Try multiple keys in a dict; return first non-None value or default."""
    for k in keys:
        v = d.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return v
    return default


def get_latest_annual_value(stmt: pd.DataFrame, row_name: str):
    """
    From a yfinance annual statement (rows = metrics, cols = dates),
    return the value for 'row_name' in the most recent column.
    Returns np.nan if not found or value is None/NaN.
    """
    if stmt is None or stmt.empty:
        return np.nan
    if row_name not in stmt.index:
        return np.nan
    # Columns are sorted newest-first by yfinance
    for col in stmt.columns:
        v = stmt.loc[row_name, col]
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return float(v), str(col.date()) if hasattr(col, "date") else str(col)
    return np.nan, "N/A"


def get_stmt_value(stmt: pd.DataFrame, row_name: str):
    """Return (value, period_str) for the most recent column in stmt."""
    if stmt is None or stmt.empty:
        return np.nan, "N/A"
    if row_name not in stmt.index:
        return np.nan, "N/A"
    for col in stmt.columns:
        v = stmt.loc[row_name, col]
        period = str(col.date()) if hasattr(col, "date") else str(col)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            try:
                return float(v), period
            except (TypeError, ValueError):
                continue
    return np.nan, "N/A"


def get_prev_annual_value(stmt: pd.DataFrame, row_name: str):
    """Return previous year's value (second column) for YoY growth calc."""
    if stmt is None or stmt.empty or row_name not in stmt.index:
        return np.nan
    cols = stmt.columns
    if len(cols) < 2:
        return np.nan
    v = stmt.loc[row_name, cols[1]]
    if v is not None and not (isinstance(v, float) and np.isnan(v)):
        try:
            return float(v)
        except (TypeError, ValueError):
            pass
    return np.nan


def pct_change(current, previous):
    """Safe percentage change. Returns NaN if either is NaN or previous == 0."""
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return np.nan
    return round(((current - previous) / abs(previous)) * 100, 4)


def safe_ratio(numerator, denominator):
    """Safe division. Returns NaN if either value is NaN or denominator is 0."""
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return round(numerator / denominator, 4)


def fetch_company_metrics(ticker_symbol: str) -> dict:
    """
    Fetch all required metrics for a single company from yfinance.
    Returns a flat dict. Missing values are np.nan (never zero-substituted).
    """
    result = {
        "Ticker":                 ticker_symbol,
        "Company_Name":           "N/A",
        "Currency":               "N/A",
        "FY_Period":              "N/A",
        # Income metrics (raw)
        "Revenue_Raw":            np.nan,
        "Revenue_Prev_Raw":       np.nan,
        "Net_Income_Raw":         np.nan,
        "Net_Income_Prev_Raw":    np.nan,
        "Gross_Profit_Raw":       np.nan,
        "Operating_Income_Raw":   np.nan,
        "EBITDA_Raw":             np.nan,
        "EPS_Diluted":            np.nan,
        # Balance sheet (raw)
        "Total_Debt_Raw":         np.nan,
        "Total_Assets_Raw":       np.nan,
        "Stockholders_Equity_Raw":np.nan,
        "Current_Assets_Raw":     np.nan,
        "Current_Liabilities_Raw":np.nan,
        # Market data
        "Current_Price":          np.nan,
        "Market_Cap_Raw":         np.nan,
        "Shares_Outstanding":     np.nan,
        # Calculated ratios (filled below)
        "Revenue_Cr":             np.nan,
        "Revenue_Growth_%":       np.nan,
        "Net_Income_Cr":          np.nan,
        "Net_Income_Growth_%":    np.nan,
        "Gross_Profit_Margin_%":  np.nan,
        "Operating_Margin_%":     np.nan,
        "Net_Profit_Margin_%":    np.nan,
        "EBITDA_Margin_%":        np.nan,
        "ROE_%":                  np.nan,
        "Debt_to_Equity":         np.nan,
        "Debt_to_Assets":         np.nan,
        "Current_Ratio":          np.nan,
        "EPS":                    np.nan,
        "PE_Ratio":               np.nan,
        "PB_Ratio":               np.nan,
        "Data_Notes":             "",
    }

    notes = []

    try:
        ticker = yf.Ticker(ticker_symbol)

        # ---- Company info ------------------------------------------------
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        result["Company_Name"] = safe_get(info, "longName", "shortName", default="N/A")
        result["Currency"]     = safe_get(info, "currency", default="N/A")

        # ---- Annual income statement -------------------------------------
        try:
            income = ticker.income_stmt
        except Exception as e:
            income = pd.DataFrame()
            notes.append(f"income_stmt error: {e}")

        # Revenue
        rev_val, rev_period = get_stmt_value(income, "Total Revenue")
        result["Revenue_Raw"] = rev_val
        result["FY_Period"]   = rev_period
        result["Revenue_Prev_Raw"] = get_prev_annual_value(income, "Total Revenue")

        # Net Income
        ni_val, _  = get_stmt_value(income, "Net Income")
        result["Net_Income_Raw"]      = ni_val
        result["Net_Income_Prev_Raw"] = get_prev_annual_value(income, "Net Income")

        # Gross Profit
        gp_val, _  = get_stmt_value(income, "Gross Profit")
        result["Gross_Profit_Raw"] = gp_val

        # Operating Income
        op_val, _  = get_stmt_value(income, "Operating Income")
        result["Operating_Income_Raw"] = op_val

        # EBITDA — try direct row first, fallback to EBIT + Depreciation
        ebitda_val, _ = get_stmt_value(income, "EBITDA")
        if pd.isna(ebitda_val):
            ebit_val, _  = get_stmt_value(income, "EBIT")
            depr_val, _  = get_stmt_value(income, "Reconciled Depreciation")
            if not pd.isna(ebit_val) and not pd.isna(depr_val):
                ebitda_val = ebit_val + depr_val
                notes.append("EBITDA derived from EBIT + Depreciation")
        result["EBITDA_Raw"] = ebitda_val

        # EPS Diluted
        eps_val, _ = get_stmt_value(income, "Diluted EPS")
        result["EPS_Diluted"] = eps_val

        # ---- Annual balance sheet ----------------------------------------
        try:
            bs = ticker.balance_sheet
        except Exception as e:
            bs = pd.DataFrame()
            notes.append(f"balance_sheet error: {e}")

        td_val,  _ = get_stmt_value(bs, "Total Debt")
        ta_val,  _ = get_stmt_value(bs, "Total Assets")
        eq_val,  _ = get_stmt_value(bs, "Stockholders Equity")
        ca_val,  _ = get_stmt_value(bs, "Current Assets")
        cl_val,  _ = get_stmt_value(bs, "Current Liabilities")

        result["Total_Debt_Raw"]          = td_val
        result["Total_Assets_Raw"]        = ta_val
        result["Stockholders_Equity_Raw"] = eq_val
        result["Current_Assets_Raw"]      = ca_val
        result["Current_Liabilities_Raw"] = cl_val

        # ---- Market data -------------------------------------------------
        price = safe_get(info, "currentPrice", "regularMarketPrice")
        if pd.isna(price):
            try:
                fi = ticker.fast_info
                price = getattr(fi, "last_price", np.nan)
            except Exception:
                price = np.nan

        shares = safe_get(info, "sharesOutstanding")
        if pd.isna(shares):
            try:
                fi = ticker.fast_info
                shares = getattr(fi, "shares", np.nan)
            except Exception:
                shares = np.nan

        mktcap = safe_get(info, "marketCap")
        if pd.isna(mktcap) and not pd.isna(price) and not pd.isna(shares):
            mktcap = price * shares

        result["Current_Price"]     = float(price)  if not pd.isna(price)  else np.nan
        result["Shares_Outstanding"]= float(shares) if not pd.isna(shares) else np.nan
        result["Market_Cap_Raw"]    = float(mktcap) if not pd.isna(mktcap) else np.nan

        # P/E from info (most reliable source)
        pe_info = safe_get(info, "trailingPE", "forwardPE")
        result["PE_Ratio"] = round(float(pe_info), 4) if not pd.isna(pe_info) else np.nan

        # P/B from info
        pb_info = safe_get(info, "priceToBook")
        result["PB_Ratio"] = round(float(pb_info), 4) if not pd.isna(pb_info) else np.nan

    except Exception as e:
        notes.append(f"General fetch error: {e}")

    result["Data_Notes"] = "; ".join(notes) if notes else "OK"

    # ===========================================================================
    # SECTION 2: CALCULATIONS
    # ===========================================================================

    rev  = result["Revenue_Raw"]
    ni   = result["Net_Income_Raw"]
    gp   = result["Gross_Profit_Raw"]
    op   = result["Operating_Income_Raw"]
    eb   = result["EBITDA_Raw"]
    eq   = result["Stockholders_Equity_Raw"]
    td   = result["Total_Debt_Raw"]
    ta   = result["Total_Assets_Raw"]
    ca   = result["Current_Assets_Raw"]
    cl   = result["Current_Liabilities_Raw"]
    eps  = result["EPS_Diluted"]
    price= result["Current_Price"]
    mktc = result["Market_Cap_Raw"]
    rev_p= result["Revenue_Prev_Raw"]
    ni_p = result["Net_Income_Prev_Raw"]

    # Crore conversions (display)
    result["Revenue_Cr"]    = round(rev / CR, 2) if not pd.isna(rev)  else np.nan
    result["Net_Income_Cr"] = round(ni  / CR, 2) if not pd.isna(ni)   else np.nan

    # Growth
    result["Revenue_Growth_%"]    = pct_change(rev, rev_p)
    result["Net_Income_Growth_%"] = pct_change(ni,  ni_p)

    # Margins
    result["Gross_Profit_Margin_%"] = round(safe_ratio(gp, rev) * 100, 4) if not pd.isna(safe_ratio(gp, rev)) else np.nan
    result["Operating_Margin_%"]    = round(safe_ratio(op, rev) * 100, 4) if not pd.isna(safe_ratio(op, rev)) else np.nan
    result["Net_Profit_Margin_%"]   = round(safe_ratio(ni, rev) * 100, 4) if not pd.isna(safe_ratio(ni, rev)) else np.nan
    result["EBITDA_Margin_%"]       = round(safe_ratio(eb, rev) * 100, 4) if not pd.isna(safe_ratio(eb, rev)) else np.nan

    # Leverage / Liquidity
    result["ROE_%"]          = round(safe_ratio(ni, eq) * 100, 4) if not pd.isna(safe_ratio(ni, eq)) else np.nan
    result["Debt_to_Equity"] = safe_ratio(td, eq)
    result["Debt_to_Assets"] = safe_ratio(td, ta)
    result["Current_Ratio"]  = safe_ratio(ca, cl)

    # EPS
    result["EPS"] = round(float(eps), 4) if not pd.isna(eps) else np.nan

    # P/E fallback: price / EPS (if not from info)
    if pd.isna(result["PE_Ratio"]) and not pd.isna(price) and not pd.isna(eps) and eps != 0:
        result["PE_Ratio"] = round(price / eps, 4)
        result["Data_Notes"] += "; PE calculated from price/EPS"

    # P/B fallback: mktcap / (equity) or price / BVPS
    if pd.isna(result["PB_Ratio"]) and not pd.isna(mktc) and not pd.isna(eq) and eq != 0:
        result["PB_Ratio"] = round(mktc / eq, 4)
        result["Data_Notes"] += "; PB calculated from mktcap/equity"

    return result


# ===========================================================================
# SECTION 3: PEER COMPARISON ORCHESTRATION
# ===========================================================================

def compare_peers(
    primary_ticker: str,
    peer_tickers: list[str],
    peer_rationale: dict = None,
    output_metrics_path: Path = OUTPUT_METRICS,
    output_comparison_path: Path = OUTPUT_COMPARISON,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch metrics for the primary company and all peers, then build
    a side-by-side comparison DataFrame.

    Args:
        primary_ticker:        Main company ticker (e.g. 'RELIANCE.NS')
        peer_tickers:          List of peer tickers
        peer_rationale:        Optional dict {ticker: reason}
        output_metrics_path:   Where to save raw metrics CSV
        output_comparison_path:Where to save formatted comparison CSV

    Returns:
        (metrics_df, comparison_df)
    """
    all_tickers = [primary_ticker] + peer_tickers
    print(f"\n  Companies to fetch: {all_tickers}")
    print(f"  Total: {len(all_tickers)} companies\n")

    all_metrics = []
    for t in all_tickers:
        print(f"  → Fetching {t} ...", end=" ", flush=True)
        m = fetch_company_metrics(t)
        status = "✓" if m["Data_Notes"] == "OK" else f"⚠ {m['Data_Notes']}"
        print(f"{m['Company_Name']} | {status}")
        all_metrics.append(m)

    metrics_df = pd.DataFrame(all_metrics)

    # ---- Comparison columns (display-friendly) ----------------------------
    comparison_cols = [
        "Ticker", "Company_Name", "Currency", "FY_Period",
        "Revenue_Cr", "Revenue_Growth_%",
        "Net_Income_Cr", "Net_Income_Growth_%",
        "Gross_Profit_Margin_%", "Operating_Margin_%",
        "Net_Profit_Margin_%", "EBITDA_Margin_%",
        "ROE_%", "Debt_to_Equity", "Debt_to_Assets", "Current_Ratio",
        "EPS", "PE_Ratio", "PB_Ratio",
        "Data_Notes",
    ]

    # Add peer rationale column
    if peer_rationale:
        metrics_df["Peer_Rationale"] = metrics_df["Ticker"].map(
            lambda t: peer_rationale.get(t, "Primary company" if t == primary_ticker else "N/A")
        )
        comparison_cols.insert(2, "Peer_Rationale")

    comparison_df = metrics_df[comparison_cols].copy()

    # ---- Save CSVs -------------------------------------------------------
    # Raw metrics (all columns including raw values for future use)
    metrics_df.to_csv(output_metrics_path, index=False)

    # Formatted comparison
    comparison_df.to_csv(output_comparison_path, index=False)

    return metrics_df, comparison_df


# ===========================================================================
# SECTION 4: REPORTING
# ===========================================================================

def print_comparison_report(comparison_df: pd.DataFrame, primary_ticker: str):
    """Print a readable peer comparison report to stdout."""

    pd.set_option("display.float_format", lambda x: f"{x:,.2f}" if not pd.isna(x) else "—")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)

    print("\n" + "=" * 80)
    print("  PEER COMPARISON REPORT")
    print("  Primary company: " + primary_ticker)
    print("  Note: Reliance is a diversified conglomerate. Peers are segment-level")
    print("        comparables, not full-company equivalents. Interpret with caution.")
    print("=" * 80)

    def section(title, cols):
        available = [c for c in cols if c in comparison_df.columns]
        if not available:
            return
        print(f"\n── {title} " + "─" * max(0, 60 - len(title)))
        sub = comparison_df[["Ticker", "Company_Name"] + available].copy()
        print(sub.to_string(index=False, na_rep="—"))

    section("Revenue & Growth (INR Crore / %)",
            ["FY_Period", "Revenue_Cr", "Revenue_Growth_%",
             "Net_Income_Cr", "Net_Income_Growth_%"])

    section("Profitability Margins (%)",
            ["Gross_Profit_Margin_%", "Operating_Margin_%",
             "Net_Profit_Margin_%", "EBITDA_Margin_%"])

    section("Returns & Leverage",
            ["ROE_%", "Debt_to_Equity", "Debt_to_Assets", "Current_Ratio"])

    section("Valuation",
            ["EPS", "PE_Ratio", "PB_Ratio"])

    # Data quality summary
    print("\n── Data Coverage ────────────────────────────────────────────────────")
    metric_cols = [
        "Revenue_Cr", "Revenue_Growth_%", "Net_Income_Cr",
        "Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%",
        "EBITDA_Margin_%", "ROE_%", "Debt_to_Equity", "Debt_to_Assets",
        "Current_Ratio", "EPS", "PE_Ratio", "PB_Ratio",
    ]
    for _, row in comparison_df.iterrows():
        available = sum(1 for m in metric_cols if m in row and not pd.isna(row[m]))
        total     = len(metric_cols)
        bar = "█" * available + "░" * (total - available)
        print(f"  {row['Ticker']:<18} [{bar}] {available}/{total} metrics available")

    print("\n── Peer Group Rationale ─────────────────────────────────────────────")
    if "Peer_Rationale" in comparison_df.columns:
        for _, row in comparison_df.iterrows():
            print(f"  {row['Ticker']:<18} {row['Peer_Rationale']}")

    print("\n── Comparability Limitations ────────────────────────────────────────")
    print("  • Reliance spans O&G, Petrochemicals, Retail, Telecom, Media,")
    print("    and New Energy — no single peer covers all segments.")
    print("  • TCS is included only as a large-cap size benchmark.")
    print("  • Margin comparisons between ONGC/IOC and HINDUNILVR are not")
    print("    meaningful due to fundamentally different business models.")
    print("  • Currency is INR for all NSE-listed peers (consistent).")
    print("  • FY periods may differ slightly; each company's most recent")
    print("    annual report period is used (shown in FY_Period column).")
    print("  • Missing values (—) indicate data was genuinely unavailable")
    print("    from yfinance; they are never substituted with zero.")
    print("=" * 80 + "\n")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def main():
    print("=" * 70)
    print("  MODULE 3 – FINANCIAL AGENT")
    print("  Feature 6: Peer Comparison")
    print("  Primary: Reliance Industries (RELIANCE.NS)")
    print("=" * 70)

    print("\n[1] Peer group selection:")
    print(f"  Primary : {DEFAULT_PRIMARY}")
    print(f"  Peers   : {DEFAULT_PEERS}")
    print("\n  Rationale:")
    for t, r in PEER_RATIONALE.items():
        print(f"    {t:<20} {r}")

    print("\n[2] Fetching financial data from Yahoo Finance (yfinance)...")
    print("  (This may take 30–60 seconds for 7 companies)")

    rationale_full = {"RELIANCE.NS": "Primary company (diversified conglomerate)"}
    rationale_full.update(PEER_RATIONALE)

    metrics_df, comparison_df = compare_peers(
        primary_ticker    = DEFAULT_PRIMARY,
        peer_tickers      = DEFAULT_PEERS,
        peer_rationale    = rationale_full,
        output_metrics_path    = OUTPUT_METRICS,
        output_comparison_path = OUTPUT_COMPARISON,
    )

    print("\n[3] Generating comparison report...")
    print_comparison_report(comparison_df, DEFAULT_PRIMARY)

    print("[4] Output files saved:")
    print(f"  → {OUTPUT_METRICS.relative_to(PROJECT_ROOT)}")
    print(f"  → {OUTPUT_COMPARISON.relative_to(PROJECT_ROOT)}")

    # Verify no existing files were modified
    existing = [
        "reliance_revenue_earnings_analysis.csv",
        "reliance_profitability_analysis.csv",
        "reliance_debt_stability_analysis.csv",
        "reliance_financial_ratios_analysis.csv",
        "reliance_historical_performance_analysis.csv",
        "reliance_historical_performance_summary.csv",
    ]
    for f in existing:
        p = DATA_DIR / f
        status = "OK (unchanged)" if p.exists() else "Missing"
        print(f"  Existing file check: {f} → {status}")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
