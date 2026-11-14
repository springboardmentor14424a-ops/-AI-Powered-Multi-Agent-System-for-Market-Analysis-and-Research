
import yfinance as yf
import pandas as pd


def get_stock_history(ticker: str, period: str = "1y"):
    """
    Fetch historical stock data from Yahoo Finance.
    """

    try:
        stock = yf.Ticker(ticker)

        data = stock.history(
            period=period,
            auto_adjust=False
        )

        if data.empty:
            return {
                "success": False,
                "message": f"No stock data found for {ticker}",
                "data": []
            }

        # Validate missing values
        data = data.dropna(
            subset=["Open", "High", "Low", "Close", "Volume"]
        )

        if data.empty:
            return {
                "success": False,
                "message": "No valid stock records available",
                "data": []
            }

        # Convert DataFrame into JSON-friendly records
        data = data.reset_index()

        records = []

        for _, row in data.iterrows():
            records.append({
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })

        return {
            "success": True,
            "ticker": ticker,
            "period": period,
            "total_records": len(records),
            "data": records
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": []
        }
