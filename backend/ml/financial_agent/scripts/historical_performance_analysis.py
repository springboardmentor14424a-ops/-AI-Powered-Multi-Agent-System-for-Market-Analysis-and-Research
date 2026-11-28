"""
historical_performance_analysis.py
-----------------------------------
Module 3 – Financial Agent | Feature 5: Historical Financial Performance Comparison

Compares Reliance Industries' financial performance across available financial years.

Metrics covered:
  - Revenue, Revenue Growth %
  - Net Income, Net Income Growth %
  - Gross Profit, Gross Profit Margin %
  - Operating Income, Operating Margin %
  - Net Profit Margin %
  - EBITDA, EBITDA Margin %
  - EPS (Diluted)
  - ROE %

Data sources (all pre-processed CSVs, no new network calls):
  - reliance_revenue_earnings_analysis.csv
  - reliance_profitability_analysis.csv
  - reliance_financial_ratios_analysis.csv

Outputs:
  - reliance_historical_performance_analysis.csv   (full year-by-year detail)
  - reliance_historical_performance_summary.csv    (trend summary per metric)

Usage (from project root):
  python backend/ml/financial_agent/scripts/historical_performance_analysis.py

Notes:
  - All monetary values are stored in raw INR (not crore).
  - Display values are shown in INR Crore (divided by 1e7).
  - Missing values are preserved as NaN, never replaced with zero.
  - YoY changes are computed only when both current and previous year values exist.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup – works from any working directory
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]          # scripts/ → financial_agent/ → ml/ → backend/ → project root
DATA_DIR = PROJECT_ROOT / "backend" / "ml" / "financial_agent" / "data" / "processed"

INPUT_FILES = {
    "revenue_earnings":  DATA_DIR / "reliance_revenue_earnings_analysis.csv",
    "profitability":     DATA_DIR / "reliance_profitability_analysis.csv",
    "ratios":            DATA_DIR / "reliance_financial_ratios_analysis.csv",
}

OUTPUT_DETAIL  = DATA_DIR / "reliance_historical_performance_analysis.csv"
OUTPUT_SUMMARY = DATA_DIR / "reliance_historical_performance_summary.csv"

CR = 1e7       # 1 Crore = 10,000,000 INR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cr(value):
    """Convert raw INR to Crore (returns NaN if value is NaN)."""
    if pd.isna(value):
        return np.nan
    return round(value / CR, 2)


def pct_change(current, previous):
    """
    Compute percentage change from previous to current.
    Returns NaN if either value is missing or previous is zero.
    """
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return np.nan
    return round(((current - previous) / abs(previous)) * 100, 4)


def abs_change(current, previous):
    """Absolute change; NaN if either value missing."""
    if pd.isna(current) or pd.isna(previous):
        return np.nan
    return round(current - previous, 2)


def trend_label(values: list):
    """
    Classify overall trend from a list of numeric values (chronological order).
    Requires at least 2 valid data points.
    Returns: 'Improving', 'Declining', 'Stable', 'Mixed', or 'Insufficient Data'
    """
    valid = [v for v in values if not pd.isna(v)]
    if len(valid) < 2:
        return "Insufficient Data"
    changes = [valid[i] - valid[i - 1] for i in range(1, len(valid))]
    pos = sum(c > 0 for c in changes)
    neg = sum(c < 0 for c in changes)
    zero = sum(c == 0 for c in changes)
    n = len(changes)
    if pos == n:
        return "Improving"
    if neg == n:
        return "Declining"
    if zero == n:
        return "Stable"
    if pos > neg:
        return "Mixed (mostly improving)"
    if neg > pos:
        return "Mixed (mostly declining)"
    return "Mixed"


def load_csv(path: Path, name: str) -> pd.DataFrame | None:
    if not path.exists():
        print(f"  [WARNING] File not found: {path.name} — {name} data will be unavailable.")
        return None
    df = pd.read_csv(path)
    # Standardise the year column
    if "Financial_Year" in df.columns:
        df["Financial_Year"] = pd.to_datetime(df["Financial_Year"], errors="coerce")
        df = df.dropna(subset=["Financial_Year"])
        df = df.sort_values("Financial_Year").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  MODULE 3 – FINANCIAL AGENT")
    print("  Feature 5: Historical Financial Performance Comparison")
    print("  Company: Reliance Industries Limited (RELIANCE.NS)")
    print("=" * 70)

    # ---- Load source CSVs ------------------------------------------------
    print("\n[1] Loading processed data files...")
    rev_df  = load_csv(INPUT_FILES["revenue_earnings"], "Revenue & Earnings")
    prof_df = load_csv(INPUT_FILES["profitability"],    "Profitability")
    rat_df  = load_csv(INPUT_FILES["ratios"],           "Financial Ratios")

    if rev_df is None and prof_df is None and rat_df is None:
        print("\n[ERROR] No source data files found. Aborting.")
        sys.exit(1)

    # ---- Collect all unique financial years --------------------------------
    all_years = set()
    for df in [rev_df, prof_df, rat_df]:
        if df is not None and "Financial_Year" in df.columns:
            all_years.update(df["Financial_Year"].tolist())

    all_years = sorted(all_years)
    print(f"  Financial years available: {[str(y.date()) for y in all_years]}")

    # ---- Build master row for each year ------------------------------------
    print("\n[2] Building year-by-year performance table...")

    def get_val(df, year, col):
        """Safe lookup: returns NaN if df is None, year missing, or column missing."""
        if df is None or col not in df.columns:
            return np.nan
        row = df[df["Financial_Year"] == year]
        if row.empty:
            return np.nan
        v = row.iloc[0][col]
        return np.nan if pd.isna(v) else v

    rows = []
    for year in all_years:
        row = {"Financial_Year": year.strftime("%Y-%m-%d")}

        # --- Revenue --------------------------------------------------------
        rev_raw          = get_val(rev_df, year, "Revenue")
        net_inc_raw      = get_val(rev_df, year, "Net_Income")
        rev_growth       = get_val(rev_df, year, "Revenue_Growth_%")
        earn_growth      = get_val(rev_df, year, "Earnings_Growth_%")

        row["Revenue_Cr"]            = cr(rev_raw)
        row["Net_Income_Cr"]         = cr(net_inc_raw)
        row["Revenue_Growth_%"]      = round(rev_growth, 4)   if not pd.isna(rev_growth)  else np.nan
        row["NetIncome_Growth_%"]    = round(earn_growth, 4)  if not pd.isna(earn_growth) else np.nan

        # --- Profitability --------------------------------------------------
        gross_raw   = get_val(prof_df, year, "Gross_Profit")
        op_raw      = get_val(prof_df, year, "Operating_Income")
        ebitda_raw  = get_val(prof_df, year, "EBITDA")

        row["Gross_Profit_Cr"]       = cr(gross_raw)
        row["Operating_Income_Cr"]   = cr(op_raw)
        row["EBITDA_Cr"]             = cr(ebitda_raw)
        row["Gross_Profit_Margin_%"] = get_val(prof_df, year, "Gross_Profit_Margin_%")
        row["Operating_Margin_%"]    = get_val(prof_df, year, "Operating_Margin_%")
        row["Net_Profit_Margin_%"]   = get_val(prof_df, year, "Net_Profit_Margin_%")
        row["EBITDA_Margin_%"]       = get_val(prof_df, year, "EBITDA_Margin_%")

        # Round margins
        for m in ["Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%", "EBITDA_Margin_%"]:
            if not pd.isna(row[m]):
                row[m] = round(row[m], 4)

        # --- Valuation ratios -----------------------------------------------
        row["EPS"]    = get_val(rat_df, year, "EPS")
        row["ROE_%"]  = get_val(rat_df, year, "ROE_%")
        for m in ["EPS", "ROE_%"]:
            if not pd.isna(row[m]):
                row[m] = round(row[m], 4)

        rows.append(row)

    detail_df = pd.DataFrame(rows)

    # ---- Year-over-year absolute & % changes --------------------------------
    print("  Calculating year-over-year changes...")

    yoy_metrics = {
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

    yoy_pct_metrics = {
        "Revenue_Cr":          "Revenue_YoY_%",
        "Net_Income_Cr":       "NetIncome_YoY_%",
        "Gross_Profit_Cr":     "GrossProfit_YoY_%",
        "Operating_Income_Cr": "OperatingIncome_YoY_%",
        "EBITDA_Cr":           "EBITDA_YoY_%",
        "EPS":                 "EPS_YoY_%",
    }

    # Absolute YoY change
    for src_col, dst_col in yoy_metrics.items():
        detail_df[dst_col] = np.nan
        for i in range(1, len(detail_df)):
            cur  = detail_df.loc[i,     src_col]
            prev = detail_df.loc[i - 1, src_col]
            detail_df.loc[i, dst_col] = abs_change(cur, prev)
        detail_df[dst_col] = detail_df[dst_col].round(4)

    # Percentage YoY change (for monetary / EPS columns)
    for src_col, dst_col in yoy_pct_metrics.items():
        detail_df[dst_col] = np.nan
        for i in range(1, len(detail_df)):
            cur  = detail_df.loc[i,     src_col]
            prev = detail_df.loc[i - 1, src_col]
            detail_df.loc[i, dst_col] = pct_change(cur, prev)
        detail_df[dst_col] = detail_df[dst_col].round(4)

    # Note: Revenue_Growth_% and NetIncome_Growth_% are already in the source
    # CSV from revenue_earnings_analysis.py — they are reused directly above.
    # The YoY_% columns here are computed independently for all other columns.

    # ---- Trend classification per metric ------------------------------------
    trend_cols = [
        "Revenue_Cr", "Net_Income_Cr", "Gross_Profit_Margin_%",
        "Operating_Margin_%", "Net_Profit_Margin_%", "EBITDA_Margin_%",
        "EPS", "ROE_%",
    ]
    trend_labels = {}
    for col in trend_cols:
        vals = detail_df[col].tolist()
        trend_labels[col] = trend_label(vals)

    # ---- Save detail CSV ---------------------------------------------------
    print("\n[3] Saving outputs...")
    detail_df.to_csv(OUTPUT_DETAIL, index=False)
    print(f"  Detail CSV → {OUTPUT_DETAIL.relative_to(PROJECT_ROOT)}")

    # ---- Build summary CSV ------------------------------------------------
    summary_rows = []
    for col in trend_cols:
        vals    = detail_df[col].dropna().tolist()
        years   = detail_df.loc[detail_df[col].notna(), "Financial_Year"].tolist()
        label   = trend_labels[col]
        first_v = vals[0]  if vals else np.nan
        last_v  = vals[-1] if vals else np.nan
        chg_abs = abs_change(last_v, first_v)
        chg_pct = pct_change(last_v, first_v)
        unit    = "INR Cr" if "_Cr" in col else ("%" if "%" in col or "ROE" in col or "EPS" == col[:3] is False else "")
        summary_rows.append({
            "Metric":                col,
            "Unit":                  "INR Cr" if "_Cr" in col else "%" if ("%" in col or "Margin" in col) else "INR" if col == "EPS" else "ratio",
            "First_Year":            years[0]  if years else "N/A",
            "First_Value":           round(first_v, 4) if not pd.isna(first_v) else np.nan,
            "Last_Year":             years[-1] if years else "N/A",
            "Last_Value":            round(last_v, 4)  if not pd.isna(last_v)  else np.nan,
            "Years_With_Data":       len(vals),
            "Absolute_Change":       round(chg_abs, 4) if not pd.isna(chg_abs) else np.nan,
            "Percentage_Change_%":   round(chg_pct, 4) if not pd.isna(chg_pct) else np.nan,
            "Overall_Trend":         label,
        })

    summary_df = pd.DataFrame(summary_rows)
    OUTPUT_SUMMARY_PATH = DATA_DIR / "reliance_historical_performance_summary.csv"
    summary_df.to_csv(OUTPUT_SUMMARY_PATH, index=False)
    print(f"  Summary CSV → {OUTPUT_SUMMARY_PATH.relative_to(PROJECT_ROOT)}")

    # ---- Print report -------------------------------------------------------
    print("\n" + "=" * 70)
    print("  HISTORICAL PERFORMANCE REPORT — RELIANCE INDUSTRIES")
    print("  All monetary values in INR Crore | Margins in % | EPS in INR")
    print("=" * 70)

    pd.set_option("display.max_columns",  None)
    pd.set_option("display.width",        200)
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}" if not pd.isna(x) else "—")

    print("\n── Revenue & Net Income ──────────────────────────────────────────────")
    rev_cols = ["Financial_Year", "Revenue_Cr", "Revenue_Growth_%",
                "Net_Income_Cr", "NetIncome_Growth_%"]
    print(detail_df[rev_cols].to_string(index=False, na_rep="—"))

    print("\n── Gross Profit & Operating Performance ─────────────────────────────")
    gp_cols = ["Financial_Year", "Gross_Profit_Cr", "Gross_Profit_Margin_%",
               "Operating_Income_Cr", "Operating_Margin_%", "Net_Profit_Margin_%"]
    print(detail_df[gp_cols].to_string(index=False, na_rep="—"))

    print("\n── EBITDA ────────────────────────────────────────────────────────────")
    eb_cols = ["Financial_Year", "EBITDA_Cr", "EBITDA_Margin_%",
               "EBITDA_YoY_Change_Cr", "EBITDA_YoY_%"]
    print(detail_df[eb_cols].to_string(index=False, na_rep="—"))

    print("\n── EPS & ROE ─────────────────────────────────────────────────────────")
    eps_cols = ["Financial_Year", "EPS", "EPS_YoY_Change", "EPS_YoY_%",
                "ROE_%", "ROE_YoY_Change_%pts"]
    print(detail_df[eps_cols].to_string(index=False, na_rep="—"))

    print("\n── Year-over-Year Monetary Changes (INR Crore) ──────────────────────")
    yoy_abs_cols = ["Financial_Year", "Revenue_YoY_Change_Cr", "Revenue_YoY_%",
                    "NetIncome_YoY_Change_Cr", "NetIncome_YoY_%",
                    "GrossProfit_YoY_Change_Cr", "OperatingIncome_YoY_Change_Cr"]
    print(detail_df[yoy_abs_cols].to_string(index=False, na_rep="—"))

    print("\n── Trend Summary ─────────────────────────────────────────────────────")
    print(f"  {'Metric':<30} {'Trend'}")
    print(f"  {'-'*30} {'-'*25}")
    for _, srow in summary_df.iterrows():
        print(f"  {srow['Metric']:<30} {srow['Overall_Trend']}")

    print("\n── Overall Insight ───────────────────────────────────────────────────")
    improving = [r["Metric"] for _, r in summary_df.iterrows() if "Improving" in r["Overall_Trend"]]
    declining = [r["Metric"] for _, r in summary_df.iterrows() if "Declining" in r["Overall_Trend"]]
    mixed     = [r["Metric"] for _, r in summary_df.iterrows() if "Mixed"     in r["Overall_Trend"]]
    insuf     = [r["Metric"] for _, r in summary_df.iterrows() if r["Overall_Trend"] == "Insufficient Data"]

    if improving: print(f"  ✅ Improving  : {', '.join(improving)}")
    if declining: print(f"  ❌ Declining  : {', '.join(declining)}")
    if mixed:     print(f"  ↕  Mixed      : {', '.join(mixed)}")
    if insuf:     print(f"  ℹ  No data    : {', '.join(insuf)}")

    print("\n── Data Coverage ─────────────────────────────────────────────────────")
    for _, srow in summary_df.iterrows():
        note = f"({srow['Years_With_Data']} year(s) of data)"
        if srow["Years_With_Data"] == 0:
            note += " — UNAVAILABLE"
        print(f"  {srow['Metric']:<30} {note}")

    print("\n" + "=" * 70)
    print("  DONE.")
    print(f"  Detail  → {OUTPUT_DETAIL.name}")
    print(f"  Summary → {OUTPUT_SUMMARY_PATH.name}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
