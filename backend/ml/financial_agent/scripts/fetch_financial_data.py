
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
print("FINANCIAL DATA FETCHER")
print("=" * 60)

print(f"\nFetching financial data for {ticker_symbol}...")

# --------------------------------------------------
# FETCH COMPANY DATA
# --------------------------------------------------

company = yf.Ticker(ticker_symbol)

# Annual income statement
income_statement = company.income_stmt

# Quarterly income statement
quarterly_income_statement = company.quarterly_income_stmt

# --------------------------------------------------
# DISPLAY ANNUAL DATA
# --------------------------------------------------

print("\n" + "=" * 60)
print("ANNUAL INCOME STATEMENT")
print("=" * 60)

if income_statement.empty:
    print("Annual income statement data is unavailable.")
else:
    print(income_statement)

# --------------------------------------------------
# DISPLAY QUARTERLY DATA
# --------------------------------------------------

print("\n" + "=" * 60)
print("QUARTERLY INCOME STATEMENT")
print("=" * 60)

if quarterly_income_statement.empty:
    print("Quarterly income statement data is unavailable.")
else:
    print(quarterly_income_statement)

# --------------------------------------------------
# SAVE DATA
# --------------------------------------------------

annual_file = DATA_DIR / "reliance_annual_income_statement.csv"
quarterly_file = DATA_DIR / "reliance_quarterly_income_statement.csv"

if not income_statement.empty:
    income_statement.to_csv(annual_file)
    print("\nAnnual data saved to:")
    print(annual_file)

if not quarterly_income_statement.empty:
    quarterly_income_statement.to_csv(quarterly_file)
    print("\nQuarterly data saved to:")
    print(quarterly_file)

print("\n" + "=" * 60)
print("DATA FETCHING COMPLETED")
print("=" * 60)

