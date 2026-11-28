
import yfinance as yf
import pandas as pd
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

DATA_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# COMPANY
# --------------------------------------------------

ticker_symbol = "RELIANCE.NS"

print("=" * 60)
print("BALANCE SHEET DATA FETCHER")
print("=" * 60)

print(f"\nFetching balance sheet data for {ticker_symbol}...")

# --------------------------------------------------
# FETCH BALANCE SHEET DATA
# --------------------------------------------------

try:
    company = yf.Ticker(ticker_symbol)

    # Annual balance sheet
    annual_balance_sheet = company.balance_sheet

    # Quarterly balance sheet
    quarterly_balance_sheet = company.quarterly_balance_sheet

except Exception as error:
    print(f"\nError occurred while fetching data from Yahoo Finance: {error}")
    annual_balance_sheet = pd.DataFrame()
    quarterly_balance_sheet = pd.DataFrame()

# --------------------------------------------------
# DISPLAY ANNUAL DATA & METRICS
# --------------------------------------------------

print("\n" + "=" * 60)
print("ANNUAL BALANCE SHEET")
print("=" * 60)

if annual_balance_sheet is None or annual_balance_sheet.empty:
    print("Annual balance sheet data is unavailable.")
else:
    print(annual_balance_sheet)

    print("\nAvailable Annual Financial Metrics (Row Names):")
    for idx, metric in enumerate(annual_balance_sheet.index, 1):
        print(f"  {idx}. {metric}")

# --------------------------------------------------
# DISPLAY QUARTERLY DATA & METRICS
# --------------------------------------------------

print("\n" + "=" * 60)
print("QUARTERLY BALANCE SHEET")
print("=" * 60)

if quarterly_balance_sheet is None or quarterly_balance_sheet.empty:
    print("Quarterly balance sheet data is unavailable.")
else:
    print(quarterly_balance_sheet)

    print("\nAvailable Quarterly Financial Metrics (Row Names):")
    for idx, metric in enumerate(quarterly_balance_sheet.index, 1):
        print(f"  {idx}. {metric}")

# --------------------------------------------------
# SAVE DATA
# --------------------------------------------------

annual_file = DATA_DIR / "reliance_annual_balance_sheet.csv"
quarterly_file = DATA_DIR / "reliance_quarterly_balance_sheet.csv"

if annual_balance_sheet is not None and not annual_balance_sheet.empty:
    annual_balance_sheet.to_csv(annual_file)
    print("\nAnnual balance sheet saved to:")
    print(annual_file)

if quarterly_balance_sheet is not None and not quarterly_balance_sheet.empty:
    quarterly_balance_sheet.to_csv(quarterly_file)
    print("\nQuarterly balance sheet saved to:")
    print(quarterly_file)

print("\n" + "=" * 60)
print("DATA FETCHING COMPLETED")
print("=" * 60)
