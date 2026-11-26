from typing import Any
import pandas as pd
import yfinance as yf


def search_stocks(query: str) -> list[dict]:
    try:
        results = yf.Search(query)
        quotes = results.quotes if hasattr(results, "quotes") else []
        return [
            {
                "symbol": q.get("symbol", ""),
                "name": q.get("shortname") or q.get("longname") or q.get("shortName") or q.get("longName", ""),
                "exchange": q.get("exchange") or q.get("exchDisp", ""),
                "type": q.get("quoteType") or q.get("typeDisp", ""),
            }
            for q in quotes
        ]
    except Exception:
        return []


def get_stock_history(symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
    try:
        from app.services.indicators import compute_all_technical_indicators
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return []
        
        enriched = compute_all_technical_indicators(hist)
        records = []
        for date, row in enriched.iterrows():
            open_val = row.get("Open") if "Open" in row else row.get("open")
            high_val = row.get("High") if "High" in row else row.get("high")
            low_val = row.get("Low") if "Low" in row else row.get("low")
            close_val = row.get("Close") if "Close" in row else row.get("close")
            vol_val = row.get("Volume") if "Volume" in row else row.get("volume")

            def _flt(k):
                v = row.get(k)
                return round(float(v), 2) if pd.notna(v) else None

            records.append({
                "date": str(date.date()) if hasattr(date, "date") else str(date),
                "open": round(float(open_val), 2) if pd.notna(open_val) else None,
                "high": round(float(high_val), 2) if pd.notna(high_val) else None,
                "low": round(float(low_val), 2) if pd.notna(low_val) else None,
                "close": round(float(close_val), 2) if pd.notna(close_val) else None,
                "volume": int(vol_val) if pd.notna(vol_val) else None,
                "sma_20": _flt("sma_20"),
                "sma_50": _flt("sma_50"),
                "sma_200": _flt("sma_200"),
                "ema_12": _flt("ema_12"),
                "ema_26": _flt("ema_26"),
                "ema_50": _flt("ema_50"),
                "rsi_14": _flt("rsi_14"),
                "macd": _flt("macd"),
                "macd_signal": _flt("macd_signal"),
                "macd_hist": _flt("macd_hist"),
            })
        return records
    except Exception:
        return []


def get_stock_quote(symbol: str) -> dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName") or info.get("longName", ""),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "exchange": info.get("exchange", ""),
            "currency": info.get("currency", ""),
        }
    except Exception:
        return {"symbol": symbol.upper(), "name": "", "price": None}
