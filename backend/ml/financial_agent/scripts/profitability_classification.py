"""
profitability_classification.py
--------------------------------
Module 3 – Financial Agent | Feature 8: Rule-Based Profitability Classification

Reusable rule-based profitability classification module that classifies
a company's profitability using real financial data (primarily Net Profit Margin),
while integrating supporting operational metrics, multi-year trend context,
and data quality validation warnings.

CLASSIFICATION TIERS:
  - Highly Profitable      : Net Profit Margin >= 15.0%
  - Moderately Profitable  : Net Profit Margin >= 5.0% and < 15.0%
  - Low Profitable         : Net Profit Margin > 0.0% and < 5.0%
  - Not Profitable         : Net Profit Margin <= 0.0%
  - Insufficient Data      : Net Profit Margin cannot be calculated or required data is missing

DISCLAIMER:
  These thresholds are our own analytical heuristics developed for the
  StockIntel Financial Agent. They are NOT official accounting standards,
  statutory regulatory definitions, or investment recommendations.
  Different sectors and industries have vastly different baseline margins.

Usage (from project root):
  python backend/ml/financial_agent/scripts/profitability_classification.py

Outputs:
  backend/ml/financial_agent/data/processed/profitability_classification.csv
  backend/ml/financial_agent/data/processed/profitability_classification_summary.csv
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup – consistent with existing project scripts
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR     = Path(__file__).resolve().parents[1] / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DETAIL  = DATA_DIR / "profitability_classification.csv"
OUTPUT_SUMMARY = DATA_DIR / "profitability_classification_summary.csv"


# ===========================================================================
# CONFIGURABLE THRESHOLD SPECIFICATION
# ===========================================================================

DEFAULT_THRESHOLDS = {
    "highly_profitable_min": 15.0,      # >= 15.0%
    "moderately_profitable_min": 5.0,   # >= 5.0% and < 15.0%
    "low_profitable_min": 0.0,          # > 0.0% and < 5.0%
    # <= 0.0% is classified as "Not Profitable"
    # NaN/missing is classified as "Insufficient Data"
}

RULE_DISCLAIMER = (
    "NOTE: These classification thresholds are analytical heuristics defined for "
    "the StockIntel Financial Agent. They are NOT official accounting standards, "
    "statutory definitions, or investment advice."
)


# ===========================================================================
# CLASSIFIER LOGIC
# ===========================================================================

def classify_margin(
    net_margin: Optional[float],
    thresholds: Dict[str, float] = DEFAULT_THRESHOLDS
) -> Tuple[str, str]:
    """
    Classify a single Net Profit Margin percentage using configurable thresholds.

    Returns:
        (classification_label, rationale)
    """
    if net_margin is None or pd.isna(net_margin):
        return "Insufficient Data", "Net Profit Margin is missing or cannot be calculated"

    try:
        val = float(net_margin)
    except (ValueError, TypeError):
        return "Insufficient Data", "Net Profit Margin is not a valid numeric value"

    hp_min = thresholds["highly_profitable_min"]
    mp_min = thresholds["moderately_profitable_min"]
    lp_min = thresholds["low_profitable_min"]

    if val >= hp_min:
        return "Highly Profitable", f"Net Profit Margin ({val:.2f}%) >= {hp_min}%"
    elif val >= mp_min:
        return "Moderately Profitable", f"Net Profit Margin ({val:.2f}%) between {mp_min}% and {hp_min}%"
    elif val > lp_min:
        return "Low Profitable", f"Net Profit Margin ({val:.2f}%) between {lp_min}% and {mp_min}%"
    else:
        return "Not Profitable", f"Net Profit Margin ({val:.2f}%) <= {lp_min}% (operating at a net loss or breakeven)"


def analyze_trend(margins: List[float]) -> str:
    """
    Identify whether margins are Improving, Declining, Stable, or Mixed over time.
    Requires chronological order (earliest to latest).
    """
    valid = [m for m in margins if not pd.isna(m)]
    if len(valid) < 2:
        return "Insufficient History"

    diffs = [valid[i] - valid[i - 1] for i in range(1, len(valid))]
    pos = sum(d > 0.05 for d in diffs)
    neg = sum(d < -0.05 for d in diffs)
    zero = sum(abs(d) <= 0.05 for d in diffs)
    n = len(diffs)

    if pos == n:
        return "Improving"
    elif neg == n:
        return "Declining"
    elif zero == n:
        return "Stable"
    elif pos > 0 and neg == 0:
        return "Improving (with stable intervals)"
    elif neg > 0 and pos == 0:
        return "Declining (with stable intervals)"
    else:
        return "Mixed"


# ===========================================================================
# REUSABLE PROFITABILITY CLASSIFIER CLASS
# ===========================================================================

class ProfitabilityClassifier:
    """
    Reusable profitability classification engine that accepts a company ticker
    and data directory, audits historical margins, extracts supporting context,
    and correlates data quality warnings.
    """

    def __init__(
        self,
        ticker: str = "RELIANCE.NS",
        data_dir: Path = DATA_DIR,
        thresholds: Dict[str, float] = None,
    ):
        self.ticker = ticker
        self.prefix = ticker.split(".")[0].lower()
        self.data_dir = data_dir
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()

    def load_inputs(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Load historical analysis, profitability analysis, and data quality report."""
        hist_file = self.data_dir / f"{self.prefix}_historical_performance_analysis.csv"
        prof_file = self.data_dir / f"{self.prefix}_profitability_analysis.csv"
        dq_file   = self.data_dir / "financial_data_quality_report.csv"

        hist_df = pd.read_csv(hist_file) if hist_file.exists() else None
        prof_df = pd.read_csv(prof_file) if prof_file.exists() else None
        dq_df   = pd.read_csv(dq_file)   if dq_file.exists()   else None

        return hist_df, prof_df, dq_df

    def classify(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Execute full classification analysis.
        Returns:
            (detail_df, summary_df)
        """
        hist_df, prof_df, dq_df = self.load_inputs()

        # Gather data quality notes by period
        dq_warnings_by_period = {}
        if dq_df is not None and not dq_df.empty:
            for _, r in dq_df.iterrows():
                p = str(r.get("Period", ""))
                sev = r.get("Severity", "")
                cat = r.get("Category", "")
                desc = r.get("Description", "")
                note = f"[{sev}] {cat}: {desc}"
                for single_p in p.split(";"):
                    sp = single_p.strip()
                    if sp:
                        dq_warnings_by_period.setdefault(sp, []).append(note)

        # Build year-by-year classification table
        # We prefer hist_df if available because it has both profitability margins and growth/ROE
        source_df = hist_df if hist_df is not None else prof_df

        if source_df is None or source_df.empty:
            print(f"[ERROR] No processed profitability data found for {self.ticker} in {self.data_dir}")
            sys.exit(1)

        source_df = source_df.sort_values("Financial_Year").reset_index(drop=True)

        detail_rows = []
        margin_series = []

        for _, r in source_df.iterrows():
            fy = str(r["Financial_Year"])
            npm = r.get("Net_Profit_Margin_%")
            gpm = r.get("Gross_Profit_Margin_%")
            opm = r.get("Operating_Margin_%")
            ebm = r.get("EBITDA_Margin_%")
            rg  = r.get("Revenue_Growth_%")
            nig = r.get("NetIncome_Growth_%")
            roe = r.get("ROE_%")

            cls_label, rationale = classify_margin(npm, self.thresholds)
            margin_series.append(npm if not pd.isna(npm) else np.nan)

            # Check for data quality warnings for this period
            p_warnings = dq_warnings_by_period.get(fy, [])
            warning_text = "; ".join(p_warnings) if p_warnings else "None"

            detail_rows.append({
                "Ticker":                 self.ticker,
                "Financial_Year":         fy,
                "Net_Profit_Margin_%":    round(npm, 4) if pd.notna(npm) else np.nan,
                "Classification":         cls_label,
                "Classification_Rationale": rationale,
                "Gross_Profit_Margin_%":  round(gpm, 4) if pd.notna(gpm) else np.nan,
                "Operating_Margin_%":     round(opm, 4) if pd.notna(opm) else np.nan,
                "EBITDA_Margin_%":        round(ebm, 4) if pd.notna(ebm) else np.nan,
                "Revenue_Growth_%":       round(rg, 4)  if pd.notna(rg)  else np.nan,
                "Net_Income_Growth_%":    round(nig, 4) if pd.notna(nig) else np.nan,
                "ROE_%":                  round(roe, 4) if pd.notna(roe) else np.nan,
                "Data_Quality_Warning":   warning_text,
            })

        detail_df = pd.DataFrame(detail_rows)

        # -------------------------------------------------------------------
        # Latest Period Summary
        # -------------------------------------------------------------------
        # Find latest period with valid data
        valid_rows = detail_df[detail_df["Net_Profit_Margin_%"].notna()]
        latest_row = valid_rows.iloc[-1] if not valid_rows.empty else detail_df.iloc[-1]

        latest_fy    = latest_row["Financial_Year"]
        latest_class = latest_row["Classification"]
        latest_npm   = latest_row["Net_Profit_Margin_%"]
        latest_rat   = latest_row["Classification_Rationale"]

        trend = analyze_trend(margin_series)

        # Data quality impact analysis
        has_critical_in_latest = "CRITICAL" in str(latest_row["Data_Quality_Warning"])
        quality_status = (
            "Caution: Critical data quality issues detected in latest period"
            if has_critical_in_latest
            else "Reliable: No critical data quality issues affect the latest evaluated period"
        )

        summary_data = [
            {"Item": "Company Ticker",                 "Value": self.ticker},
            {"Item": "Primary Evaluation Metric",      "Value": "Net Profit Margin (%)"},
            {"Item": "Latest Evaluated Financial Year", "Value": str(latest_fy)},
            {"Item": "Latest Net Profit Margin (%)",    "Value": f"{latest_npm:.2f}%" if pd.notna(latest_npm) else "N/A"},
            {"Item": "Overall Profitability Class",    "Value": latest_class},
            {"Item": "Classification Rationale",       "Value": latest_rat},
            {"Item": "Multi-Year Margin Trend",        "Value": trend},
            {"Item": "Gross Profit Margin (%)",        "Value": f"{latest_row['Gross_Profit_Margin_%']:.2f}%" if pd.notna(latest_row['Gross_Profit_Margin_%']) else "N/A"},
            {"Item": "Operating Profit Margin (%)",    "Value": f"{latest_row['Operating_Margin_%']:.2f}%" if pd.notna(latest_row['Operating_Margin_%']) else "N/A"},
            {"Item": "EBITDA Margin (%)",              "Value": f"{latest_row['EBITDA_Margin_%']:.2f}%" if pd.notna(latest_row['EBITDA_Margin_%']) else "N/A"},
            {"Item": "Revenue Growth YoY (%)",         "Value": f"{latest_row['Revenue_Growth_%']:.2f}%" if pd.notna(latest_row['Revenue_Growth_%']) else "N/A"},
            {"Item": "Net Income Growth YoY (%)",      "Value": f"{latest_row['Net_Income_Growth_%']:.2f}%" if pd.notna(latest_row['Net_Income_Growth_%']) else "N/A"},
            {"Item": "Return on Equity ROE (%)",       "Value": f"{latest_row['ROE_%']:.2f}%" if pd.notna(latest_row['ROE_%']) else "N/A"},
            {"Item": "Data Quality Status",            "Value": quality_status},
            {"Item": "Data Quality Warning for Latest Period", "Value": latest_row["Data_Quality_Warning"]},
            {"Item": "Configured Threshold - Highly Profitable", "Value": f">= {self.thresholds['highly_profitable_min']}%"},
            {"Item": "Configured Threshold - Moderately Profitable", "Value": f">= {self.thresholds['moderately_profitable_min']}% and < {self.thresholds['highly_profitable_min']}%"},
            {"Item": "Configured Threshold - Low Profitable", "Value": f"> {self.thresholds['low_profitable_min']}% and < {self.thresholds['moderately_profitable_min']}%"},
            {"Item": "Configured Threshold - Not Profitable", "Value": f"<= {self.thresholds['low_profitable_min']}%"},
            {"Item": "Rule Disclaimer",                "Value": RULE_DISCLAIMER},
        ]
        summary_df = pd.DataFrame(summary_data)

        # Save files
        detail_df.to_csv(OUTPUT_DETAIL, index=False)
        summary_df.to_csv(OUTPUT_SUMMARY, index=False)

        return detail_df, summary_df


# ===========================================================================
# REPORTING
# ===========================================================================

def print_classification_report(detail_df: pd.DataFrame, summary_df: pd.DataFrame):
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)

    print("\n" + "=" * 80)
    print("  RULE-BASED PROFITABILITY CLASSIFICATION REPORT")
    print("  StockIntel Financial Agent — Module 3 Core Feature 8")
    print("=" * 80)

    print("\n" + RULE_DISCLAIMER)

    print("\n── 1. Executive Classification Summary ─────────────────────────────────")
    for _, r in summary_df.iterrows():
        print(f"  {r['Item']:<40} : {r['Value']}")

    print("\n── 2. Historical Year-by-Year Classification ──────────────────────────")
    display_cols = [
        "Financial_Year", "Net_Profit_Margin_%", "Classification",
        "Gross_Profit_Margin_%", "Operating_Margin_%", "EBITDA_Margin_%",
        "Revenue_Growth_%", "ROE_%"
    ]
    sub = detail_df[display_cols].copy()
    print(sub.to_string(index=False, na_rep="—"))

    print("\n── 3. Data Quality Warnings by Period ─────────────────────────────────")
    for _, r in detail_df.iterrows():
        fy = r["Financial_Year"]
        warn = r["Data_Quality_Warning"]
        cls_name = r["Classification"]
        status_icon = "⚠️" if warn != "None" else "✅"
        print(f"  {status_icon} FY {fy} [{cls_name}]: {warn}")

    print("\n" + "=" * 80)
    print(f"  Detailed Results Saved → {OUTPUT_DETAIL.name}")
    print(f"  Summary Results Saved  → {OUTPUT_SUMMARY.name}")
    print("=" * 80 + "\n")


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================

def main():
    classifier = ProfitabilityClassifier(ticker="RELIANCE.NS", data_dir=DATA_DIR)
    detail_df, summary_df = classifier.classify()
    print_classification_report(detail_df, summary_df)


if __name__ == "__main__":
    main()
