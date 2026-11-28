
import yfinance as yf

# Download historical stock data
stock = yf.Ticker("INFY.NS")
data = stock.history(period="1y")

# Calculate moving averages
data["MA50"] = data["Close"].rolling(window=50).mean()
data["MA200"] = data["Close"].rolling(window=200).mean()

# Get latest and previous values
today_ma50 = data["MA50"].iloc[-1]
today_ma200 = data["MA200"].iloc[-1]

yesterday_ma50 = data["MA50"].iloc[-2]
yesterday_ma200 = data["MA200"].iloc[-2]

# Detect Golden Cross
if yesterday_ma50 <= yesterday_ma200 and today_ma50 > today_ma200:
    print("Golden Cross detected! Bullish signal.")
else:
    print("No Golden Cross detected.")
