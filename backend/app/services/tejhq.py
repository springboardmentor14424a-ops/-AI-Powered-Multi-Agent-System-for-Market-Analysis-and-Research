
import requests
from datetime import datetime, date, timedelta

from app.services.yahoo_finance import get_stock_history as get_yahoo_stock_history

BASE_URL = "https://api.tejhq.dev/v1/ohlcv/bse"

# Mapping of common BSE numeric security codes to their trading symbols
BSE_CODE_MAP = {
    "532540": "TCS",
    "500325": "RELIANCE",
    "500209": "INFY",
    "500180": "HDFCBANK",
    "532215": "ICICIBANK",
    "500570": "TATAMOTORS",
    "500696": "HINDUNILVR",
    "500112": "SBIN",
    "500820": "ASIANPAINT",
    "500875": "ITC",
    "507685": "WIPRO",
    "532454": "BHARTIARTL",
    "500470": "TATASTEEL",
    "500510": "LT",
    "532500": "MARUTI",
    "500247": "KOTAKBANK",
    "532174": "ICICIBANK",
    "532555": "NTPC",
    "500312": "ONGC",
    "532977": "BAJAJ-AUTO",
}


def get_bse_stock_history(ticker: str, period: str = "1y"):
    """
    Fetch BSE historical stock data using TejHQ with automatic Yahoo Finance fallback.
    Returns data in a common OHLCV format.
    """
    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "5y": 1825
    }

    if period not in period_days:
        return {
            "success": False,
            "message": "Invalid analysis period",
            "data": []
        }

    # Clean symbol: remove .BO or .NS suffix if present
    symbol = ticker.upper().strip()
    if symbol.endswith(".BO") or symbol.endswith(".NS"):
        symbol = symbol[:-3]

    # Map numeric scrip code if provided (e.g. 532540 -> TCS)
    symbol = BSE_CODE_MAP.get(symbol, symbol)

    url = f"{BASE_URL}/{symbol}"

    # Step 1: Try TejHQ API with all historical data starting from 2024-01-01
    try:
        response = requests.get(
            url,
            params={"from": "2024-01-01"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; StockIntel/1.0)"},
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            raw_records = result.get("data", [])

            if raw_records:
                records = []
                required_fields = ["date", "open", "high", "low", "close", "volume"]

                for item in raw_records:
                    if not all(item.get(field) is not None for field in required_fields):
                        continue

                    records.append({
                        "date": item["date"],
                        "open": float(item["open"]),
                        "high": float(item["high"]),
                        "low": float(item["low"]),
                        "close": float(item["close"]),
                        "volume": int(item["volume"])
                    })

                if records:
                    # Sort ascending by date
                    records.sort(key=lambda x: x["date"])

                    # Filter records according to the requested period relative to the latest available date
                    try:
                        latest_dt = datetime.strptime(records[-1]["date"], "%Y-%m-%d").date()
                        cutoff_dt = latest_dt - timedelta(days=period_days[period])
                        filtered = [r for r in records if datetime.strptime(r["date"], "%Y-%m-%d").date() >= cutoff_dt]
                        if filtered:
                            records = filtered
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "ticker": symbol,
                        "market": "BSE",
                        "period": period,
                        "total_records": len(records),
                        "data": records
                    }
    except Exception:
        # Pass to Yahoo Finance fallback
        pass

    # Step 2: Fallback to Yahoo Finance with .BO suffix if TejHQ failed or returned no data
    try:
        yahoo_ticker = f"{symbol}.BO"
        yahoo_res = get_yahoo_stock_history(yahoo_ticker, period)
        if yahoo_res.get("success") and yahoo_res.get("data"):
            yahoo_res["market"] = "BSE"
            yahoo_res["ticker"] = symbol
            return yahoo_res
    except Exception:
        pass

    return {
        "success": False,
        "message": f"No BSE data found for {symbol}",
        "data": []
    }
