
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

OUTPUT_FILE = DATA_DIR / "reliance_market_price_history.csv"

# --------------------------------------------------
# COMPANY
# --------------------------------------------------

ticker_symbol = "RELIANCE.NS"

print("=" * 60)
print("MARKET DATA FETCHER")
print("=" * 60)

print(f"\nFetching market data for {ticker_symbol}...")

# --------------------------------------------------
# FETCH CURRENT MARKET DATA
# --------------------------------------------------

current_price = None
shares_outstanding = None
market_cap = None
currency = "INR"

try:
    company = yf.Ticker(ticker_symbol)

    # Attempt to retrieve information from company info
    info = company.info or {}
    fast_info = getattr(company, "fast_info", None)

    # 1. Current / Latest stock price
    if info.get("currentPrice") is not None:
        current_price = float(info["currentPrice"])
    elif info.get("regularMarketPrice") is not None:
        current_price = float(info["regularMarketPrice"])
    elif fast_info and getattr(fast_info, "last_price", None) is not None:
        current_price = float(fast_info.last_price)

    # 2. Shares outstanding
    if info.get("sharesOutstanding") is not None:
        shares_outstanding = int(info["sharesOutstanding"])
    elif fast_info and getattr(fast_info, "shares", None) is not None:
        shares_outstanding = int(fast_info.shares)

    # 3. Market capitalization
    if info.get("marketCap") is not None:
        market_cap = float(info["marketCap"])
    elif fast_info and getattr(fast_info, "market_cap", None) is not None:
        market_cap = float(fast_info.market_cap)
    elif current_price is not None and shares_outstanding is not None:
        market_cap = float(current_price * shares_outstanding)

    currency = info.get("currency", "INR")

except Exception as error:
    print(f"\nError occurred while fetching company info: {error}")

# --------------------------------------------------
# FETCH 5-YEAR HISTORICAL PRICE DATA
# --------------------------------------------------

price_history = pd.DataFrame()

try:
    print("\nFetching 5-year historical stock prices...")
    price_history = company.history(period="5y")

    # If current_price was still not found, fallback to latest close
    if current_price is None and not price_history.empty:
        current_price = float(price_history["Close"].iloc[-1])
        if shares_outstanding is not None and market_cap is None:
            market_cap = float(current_price * shares_outstanding)

except Exception as error:
    print(f"\nError occurred while fetching historical prices: {error}")

# --------------------------------------------------
# DISPLAY FETCHED MARKET DATA
# --------------------------------------------------

print("\n" + "=" * 60)
print("CURRENT MARKET SUMMARY")
print("=" * 60)

print(f"\nTicker Symbol:         {ticker_symbol}")

# Current Price
if current_price is not None:
    print(f"Current Stock Price:   ₹{current_price:,.2f}")
else:
    print("Current Stock Price:   Unavailable")

# Shares Outstanding
if shares_outstanding is not None:
    print(f"Shares Outstanding:    {shares_outstanding:,}")
else:
    print("Shares Outstanding:    Unavailable")

# Market Capitalization
if market_cap is not None:
    market_cap_crores = market_cap / 1e7
    print(f"Market Capitalization: ₹{market_cap:,.2f} (₹{market_cap_crores:,.2f} Cr)")
else:
    print("Market Capitalization: Unavailable")

# --------------------------------------------------
# DISPLAY & SAVE HISTORICAL DATA
# --------------------------------------------------

print("\n" + "=" * 60)
print("HISTORICAL PRICE DATA (LAST 5 YEARS)")
print("=" * 60)

if price_history.empty:
    print("\nNo historical stock price data available to save.")
else:
    # Clean Date index formatting
    clean_history = price_history.copy()
    clean_history.index = pd.to_datetime(clean_history.index).strftime("%Y-%m-%d")
    clean_history.index.name = "Date"

    print(f"\nTotal Trading Days Retrieved: {len(clean_history)}")
    print(f"Date Range: {clean_history.index[0]} to {clean_history.index[-1]}")

    print("\nRecent 5 Trading Days:")
    display_columns = [col for col in ["Open", "High", "Low", "Close", "Volume"] if col in clean_history.columns]
    print(clean_history[display_columns].tail().to_string())

    # Save to CSV
    clean_history.to_csv(OUTPUT_FILE)
    print("\n" + "=" * 60)
    print("HISTORICAL PRICE DATA SAVED")
    print("=" * 60)
    print(f"\nSaved to: {OUTPUT_FILE}")

print("\n" + "=" * 60)
print("MARKET DATA FETCHING COMPLETED!")
print("=" * 60)
