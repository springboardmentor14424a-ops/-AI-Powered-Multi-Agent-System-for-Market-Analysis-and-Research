
import pandas as pd
import numpy as np
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATA_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
)

INPUT_FILE = DATA_DIR / "reliance_annual_balance_sheet.csv"

OUTPUT_FILE = DATA_DIR / "reliance_debt_stability_analysis.csv"

print("=" * 60)
print("DEBT & FINANCIAL STABILITY ANALYSIS")
print("=" * 60)

# --------------------------------------------------
# SAFE DIVISION HELPER
# --------------------------------------------------

def safe_divide(numerator, denominator):
    """
    Safely divide numerator by denominator handling zero and missing values.
    Returns np.nan if denominator is zero or if either value is missing.
    Does not replace missing financial data with zero.
    """
    safe_denom = denominator.replace(0, np.nan)
    return numerator / safe_denom

# --------------------------------------------------
# LOAD BALANCE SHEET DATA
# --------------------------------------------------

try:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    # Read the annual balance sheet CSV
    df = pd.read_csv(INPUT_FILE, index_col=0)

    # Convert columns (dates) into rows representing financial years
    df = df.T

    # Convert index to datetime to preserve chronological order
    df.index = pd.to_datetime(df.index)

    # Sort financial years from oldest to newest
    df = df.sort_index()

except Exception as error:
    print(f"\nError occurred while loading data: {error}")
    raise SystemExit(1)

# --------------------------------------------------
# VERIFY REQUIRED FINANCIAL METRICS
# --------------------------------------------------

required_metrics = [
    "Total Debt",
    "Net Debt",
    "Total Assets",
    "Stockholders Equity",
    "Current Assets",
    "Current Liabilities",
    "Cash And Cash Equivalents"
]

missing_metrics = [m for m in required_metrics if m not in df.columns]

if missing_metrics:
    print(f"\nError: Missing required financial metrics in CSV: {missing_metrics}")
    raise SystemExit(1)

# --------------------------------------------------
# EXTRACT RAW FINANCIAL METRICS
# --------------------------------------------------

analysis = pd.DataFrame(index=df.index)

analysis["Total_Debt"] = df["Total Debt"]
analysis["Net_Debt"] = df["Net Debt"]
analysis["Total_Assets"] = df["Total Assets"]
analysis["Stockholders_Equity"] = df["Stockholders Equity"]
analysis["Current_Assets"] = df["Current Assets"]
analysis["Current_Liabilities"] = df["Current Liabilities"]
analysis["Cash_And_Cash_Equivalents"] = df["Cash And Cash Equivalents"]

# --------------------------------------------------
# CALCULATE DEBT & STABILITY RATIOS
# --------------------------------------------------

# 1. Debt-to-Equity Ratio = Total Debt / Stockholders Equity
analysis["Debt_to_Equity_Ratio"] = safe_divide(
    analysis["Total_Debt"],
    analysis["Stockholders_Equity"]
)

# 2. Debt-to-Assets Ratio = Total Debt / Total Assets
analysis["Debt_to_Assets_Ratio"] = safe_divide(
    analysis["Total_Debt"],
    analysis["Total_Assets"]
)

# 3. Current Ratio = Current Assets / Current Liabilities
analysis["Current_Ratio"] = safe_divide(
    analysis["Current_Assets"],
    analysis["Current_Liabilities"]
)

# 4. Cash-to-Debt Ratio = Cash And Cash Equivalents / Total Debt
analysis["Cash_to_Debt_Ratio"] = safe_divide(
    analysis["Cash_And_Cash_Equivalents"],
    analysis["Total_Debt"]
)

# 5. Net Debt-to-Assets Ratio = Net Debt / Total Assets
analysis["Net_Debt_to_Assets_Ratio"] = safe_divide(
    analysis["Net_Debt"],
    analysis["Total_Assets"]
)

# --------------------------------------------------
# FORMAT FINANCIAL YEAR AND SAVE RESULTS
# --------------------------------------------------

analysis = analysis.reset_index()

analysis = analysis.rename(
    columns={"index": "Financial_Year"}
)

# Format Financial_Year as YYYY-MM-DD string
analysis["Financial_Year"] = pd.to_datetime(
    analysis["Financial_Year"]
).dt.strftime("%Y-%m-%d")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

analysis.to_csv(OUTPUT_FILE, index=False)

# --------------------------------------------------
# DISPLAY SUMMARY OF CALCULATED METRICS
# --------------------------------------------------

print("\nAnnual Debt & Financial Stability Metrics:\n")

ratio_columns = [
    "Financial_Year",
    "Debt_to_Equity_Ratio",
    "Debt_to_Assets_Ratio",
    "Current_Ratio",
    "Cash_to_Debt_Ratio",
    "Net_Debt_to_Assets_Ratio"
]

# Display table with rounded ratio values for readability
display_df = analysis[ratio_columns].copy()
for col in ratio_columns[1:]:
    display_df[col] = display_df[col].round(4)

print(display_df.to_string(index=False))

# --------------------------------------------------
# LATEST FINANCIAL YEAR SUMMARY
# --------------------------------------------------

latest = analysis.iloc[-1]

print("\n" + "=" * 60)
print("LATEST FINANCIAL STABILITY SUMMARY")
print("=" * 60)

print(f"\nFinancial Year: {latest['Financial_Year']}")

print("\nKey Ratios:")
print(f"  Debt-to-Equity Ratio:     {latest['Debt_to_Equity_Ratio']:.4f}")
print(f"  Debt-to-Assets Ratio:     {latest['Debt_to_Assets_Ratio']:.4f}")
print(f"  Current Ratio:            {latest['Current_Ratio']:.4f}")
print(f"  Cash-to-Debt Ratio:       {latest['Cash_to_Debt_Ratio']:.4f}")
print(f"  Net Debt-to-Assets Ratio: {latest['Net_Debt_to_Assets_Ratio']:.4f}")

print("\nUnderlying Balances (in ₹ Crores):")
print(f"  Total Debt:               ₹{latest['Total_Debt'] / 1e7:,.2f} Cr")
print(f"  Net Debt:                 ₹{latest['Net_Debt'] / 1e7:,.2f} Cr")
print(f"  Stockholders Equity:      ₹{latest['Stockholders_Equity'] / 1e7:,.2f} Cr")
print(f"  Total Assets:             ₹{latest['Total_Assets'] / 1e7:,.2f} Cr")
print(f"  Current Assets:           ₹{latest['Current_Assets'] / 1e7:,.2f} Cr")
print(f"  Current Liabilities:      ₹{latest['Current_Liabilities'] / 1e7:,.2f} Cr")
print(f"  Cash & Equivalents:       ₹{latest['Cash_And_Cash_Equivalents'] / 1e7:,.2f} Cr")

# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 60)
print("DEBT & STABILITY ANALYSIS COMPLETED!")
print("=" * 60)

print("\nSaved to:")
print(OUTPUT_FILE)
