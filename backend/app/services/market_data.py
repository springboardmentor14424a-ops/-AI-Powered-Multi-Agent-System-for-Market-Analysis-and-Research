import yfinance as yf
import pandas as pd

def fetch_stock_market_data(ticker: str, period: str = "1y"):
    """
    Fetches live stock market data, fundamentals, and historical pricing.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)
        
        if hist.empty:
            raise ValueError(f"No market data found for ticker: {ticker}")
            
        info = stock.info
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or hist['Close'].iloc[-1]
        previous_close = info.get("previousClose") or hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change_pct = ((current_price - previous_close) / previous_close) * 100 if previous_close else 0.0

        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName", ticker.upper()),
            "current_price": round(float(current_price), 2),
            "previous_close": round(float(previous_close), 2),
            "change_percent": round(float(change_pct), 2),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "history_records": len(hist)
        }
    except Exception as e:
        raise RuntimeError(f"Market data fetch failed: {str(e)}")