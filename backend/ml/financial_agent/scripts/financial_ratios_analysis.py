
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

INCOME_FILE = DATA_DIR / "reliance_annual_income_statement.csv"
BALANCE_FILE = DATA_DIR / "reliance_annual_balance_sheet.csv"
MARKET_FILE = DATA_DIR / "reliance_market_price_history.csv"

OUTPUT_FILE = DATA_DIR / "reliance_financial_ratios_analysis.csv"

print("=" * 60)
print("FINANCIAL RATIOS ANALYSIS")
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
    if isinstance(denominator, pd.Series):
        safe_denom = denominator.replace(0, np.nan)
    else:
        safe_denom = np.nan if denominator == 0 else denominator

    return numerator / safe_denom

# --------------------------------------------------
# LOAD INPUT CSV FILES WITH ERROR HANDLING
# --------------------------------------------------

try:
    # Check that all required input files exist
    for file_path in [INCOME_FILE, BALANCE_FILE, MARKET_FILE]:
        if not file_path.exists():
            raise FileNotFoundError(f"Required input file not found: {file_path}")

    # 1. Load annual income statement
    income_raw = pd.read_csv(INCOME_FILE, index_col=0)
    income_df = income_raw.T
    income_df.index = pd.to_datetime(income_df.index)

    # 2. Load annual balance sheet
    balance_raw = pd.read_csv(BALANCE_FILE, index_col=0)
    balance_df = balance_raw.T
    balance_df.index = pd.to_datetime(balance_df.index)

    # 3. Load market price history
    market_df = pd.read_csv(MARKET_FILE, index_col=0)
    market_df.index = pd.to_datetime(market_df.index)

except Exception as error:
    print(f"\nError occurred while loading input files: {error}")
    raise SystemExit(1)

# --------------------------------------------------
# VALIDATE REQUIRED FINANCIAL METRICS
# --------------------------------------------------

# Required metric in income statement
if "Net Income" not in income_df.columns:
    print("\nError: 'Net Income' row missing in income statement CSV.")
    raise SystemExit(1)

# Required metrics in balance sheet
required_balance_metrics = ["Stockholders Equity", "Ordinary Shares Number"]
missing_balance = [m for m in required_balance_metrics if m not in balance_df.columns]
if missing_balance:
    print(f"\nError: Missing required balance sheet metrics: {missing_balance}")
    raise SystemExit(1)

# Required column in market price history
if "Close" not in market_df.columns or market_df.empty:
    print("\nError: 'Close' price column missing or market price history is empty.")
    raise SystemExit(1)

# --------------------------------------------------
# EXTRACT LATEST STOCK MARKET DATA
# --------------------------------------------------

latest_price_date = market_df.index[-1].strftime("%Y-%m-%d")
latest_stock_price = float(market_df["Close"].iloc[-1])

print(f"\nLatest Stock Price: ₹{latest_stock_price:,.2f} (as of {latest_price_date})")

# --------------------------------------------------
# ALIGN FINANCIAL YEARS (CHRONOLOGICAL ORDER)
# --------------------------------------------------

# Union of financial years from both statements, sorted chronologically
all_years = income_df.index.union(balance_df.index).sort_values()

analysis = pd.DataFrame(index=all_years)

# Extract raw financial figures matching by financial year
analysis["Net_Income"] = income_df["Net Income"]
analysis["Stockholders_Equity"] = balance_df["Stockholders Equity"]
analysis["Ordinary_Shares_Number"] = balance_df["Ordinary Shares Number"]

# --------------------------------------------------
# CALCULATE HISTORICAL FINANCIAL RATIOS
# --------------------------------------------------

# 1. Return on Equity (ROE) % = (Net Income / Stockholders Equity) * 100
analysis["ROE_%"] = (
    safe_divide(analysis["Net_Income"], analysis["Stockholders_Equity"]) * 100
)

# 2. Earnings Per Share (EPS) = Net Income / Ordinary Shares Number
analysis["EPS"] = safe_divide(
    analysis["Net_Income"],
    analysis["Ordinary_Shares_Number"]
)

# Book Value Per Share = Stockholders Equity / Ordinary Shares Number
analysis["Book_Value_Per_Share"] = safe_divide(
    analysis["Stockholders_Equity"],
    analysis["Ordinary_Shares_Number"]
)

# --------------------------------------------------
# CALCULATE LATEST VALUATION RATIOS (P/E & P/B)
# --------------------------------------------------

# Identify the latest financial year that has valid EPS and BVPS
valid_years = analysis.dropna(subset=["EPS", "Book_Value_Per_Share"])

if valid_years.empty:
    print("\nWarning: No financial year with valid EPS and Book Value found.")
    latest_fy_date = "N/A"
    latest_eps = np.nan
    latest_bvps = np.nan
    latest_pe = np.nan
    latest_pb = np.nan
else:
    latest_fy_index = valid_years.index[-1]
    latest_fy_date = latest_fy_index.strftime("%Y-%m-%d")
    latest_eps = float(valid_years.loc[latest_fy_index, "EPS"])
    latest_bvps = float(valid_years.loc[latest_fy_index, "Book_Value_Per_Share"])

    # 3. Price-to-Earnings Ratio (P/E) = Latest stock price / latest available EPS
    latest_pe = safe_divide(latest_stock_price, latest_eps)

    # 4. Price-to-Book Ratio (P/B) = Latest stock price / Book Value Per Share
    latest_pb = safe_divide(latest_stock_price, latest_bvps)

# Add valuation columns to analysis dataframe for the latest financial year
analysis["Latest_Stock_Price"] = np.nan
analysis["Stock_Price_Date"] = ""
analysis["PE_Ratio"] = np.nan
analysis["PB_Ratio"] = np.nan

if not valid_years.empty:
    analysis.loc[latest_fy_index, "Latest_Stock_Price"] = latest_stock_price
    analysis.loc[latest_fy_index, "Stock_Price_Date"] = latest_price_date
    analysis.loc[latest_fy_index, "PE_Ratio"] = latest_pe
    analysis.loc[latest_fy_index, "PB_Ratio"] = latest_pb

# --------------------------------------------------
# FORMAT FINANCIAL YEAR AND SAVE RESULTS
# --------------------------------------------------

analysis = analysis.reset_index()
analysis = analysis.rename(columns={"index": "Financial_Year"})
analysis["Financial_Year"] = pd.to_datetime(analysis["Financial_Year"]).dt.strftime("%Y-%m-%d")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
analysis.to_csv(OUTPUT_FILE, index=False)

# --------------------------------------------------
# DISPLAY SUMMARY OF RESULTS
# --------------------------------------------------

print("\n" + "=" * 60)
print("HISTORICAL FINANCIAL RATIOS")
print("=" * 60)

display_cols = [
    "Financial_Year",
    "Net_Income",
    "Stockholders_Equity",
    "Ordinary_Shares_Number",
    "ROE_%",
    "EPS",
    "Book_Value_Per_Share"
]

display_df = analysis[display_cols].copy()

# Format for clean terminal display
display_df["Net_Income (Cr)"] = display_df["Net_Income"].apply(
    lambda x: f"₹{x / 1e7:,.2f} Cr" if pd.notna(x) else "—"
)
display_df["Equity (Cr)"] = display_df["Stockholders_Equity"].apply(
    lambda x: f"₹{x / 1e7:,.2f} Cr" if pd.notna(x) else "—"
)
display_df["Shares (Cr)"] = display_df["Ordinary_Shares_Number"].apply(
    lambda x: f"{x / 1e7:,.2f} Cr" if pd.notna(x) else "—"
)
display_df["ROE (%)"] = display_df["ROE_%"].apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
)
display_df["EPS (₹)"] = display_df["EPS"].apply(
    lambda x: f"₹{x:.2f}" if pd.notna(x) else "—"
)
display_df["BVPS (₹)"] = display_df["Book_Value_Per_Share"].apply(
    lambda x: f"₹{x:.2f}" if pd.notna(x) else "—"
)

summary_table_cols = [
    "Financial_Year",
    "Net_Income (Cr)",
    "Equity (Cr)",
    "Shares (Cr)",
    "ROE (%)",
    "EPS (₹)",
    "BVPS (₹)"
]

print("\n" + display_df[summary_table_cols].to_string(index=False))

# --------------------------------------------------
# LATEST VALUATION SUMMARY (P/E & P/B)
# --------------------------------------------------

print("\n" + "=" * 60)
print("LATEST VALUATION RATIOS SUMMARY")
print("=" * 60)

print(f"\nValuation Inputs:")
print(f"  Stock Price Used:       ₹{latest_stock_price:,.2f}")
print(f"  Stock Price Date:       {latest_price_date}")
print(f"  Financial Year Used:    {latest_fy_date}")
print(f"  Latest Available EPS:   ₹{latest_eps:.2f}")
print(f"  Book Value Per Share:   ₹{latest_bvps:.2f}")

print(f"\nCalculated Valuation Ratios:")
print(f"  Price-to-Earnings (P/E): {latest_pe:.2f}x")
print(f"  Price-to-Book (P/B):     {latest_pb:.2f}x")

# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 60)
print("FINANCIAL RATIOS ANALYSIS COMPLETED!")
print("=" * 60)

print(f"\nSaved results to:\n{OUTPUT_FILE}")
