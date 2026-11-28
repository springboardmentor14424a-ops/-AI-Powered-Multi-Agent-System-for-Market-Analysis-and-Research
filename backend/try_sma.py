import yfinance as yf
from technical_analysis import calculate_sma, calculate_ema

# Get the last 6 months of RELIANCE closing prices from Yahoo Finance
data = yf.Ticker("RELIANCE.NS").history(period="6mo")
close = data["Close"]

# Calculate 20-day SMA and 20-day EMA
sma20 = calculate_sma(close, 20)
ema20 = calculate_ema(close, 20)

print("Latest close price:", round(close.iloc[-1], 2))
print("20-day SMA:", round(sma20.iloc[-1], 2))
print("20-day EMA:", round(ema20.iloc[-1], 2))

# Hand check: average of the last 20 closing prices
print("Hand check (average of last 20 closes):", round(close.iloc[-20:].mean(), 2))
