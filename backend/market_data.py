import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

# Map user preference periods to Yahoo Finance format
PERIOD_MAP = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
}

def format_ticker_for_market(symbol: str, market: str = "NASDAQ") -> str:
    """Appends the correct exchange suffix for Indian markets (NSE/BSE)."""
    clean_symbol = symbol.strip().upper()
    market_upper = market.strip().upper()

    if market_upper == "NSE" and not clean_symbol.endswith(".NS"):
        return f"{clean_symbol}.NS"
    elif market_upper == "BSE" and not clean_symbol.endswith(".BO"):
        return f"{clean_symbol}.BO"
    return clean_symbol

def search_companies(query: str, max_results: int = 8) -> dict:
    """Search for companies by name or ticker symbol using Yahoo Finance."""
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        search = yf.Search(query, max_results=max_results)
        quotes = search.quotes or []
        results = [
            {
                "symbol": q.get("symbol"),
                "name": q.get("shortname") or q.get("longname") or q.get("symbol"),
                "exchange": q.get("exchange"),
                "quote_type": q.get("quoteType"),
            }
            for q in quotes
            if q.get("symbol") and q.get("quoteType") == "EQUITY"
        ]
        return {
            "query": query,
            "results": results,
            "source": "Yahoo Finance",
            "retrieved_at": retrieved_at,
        }
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "error": str(e),
            "source": "Yahoo Finance",
            "retrieved_at": retrieved_at,
        }

def validate_and_clean_ohlcv(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """
    Validates historical OHLCV data for missing values, duplicate dates,
    and inconsistent prices/volumes, returning cleaned records and a report.
    """
    validation_report = {
        "total_rows_raw": len(df),
        "duplicate_dates_removed": 0,
        "missing_values_dropped": 0,
        "inconsistent_rows_removed": 0,
        "is_valid": True,
    }

    if df.empty:
        validation_report["is_valid"] = False
        return [], validation_report

    # 1. Remove duplicate dates
    dup_count = int(df.index.duplicated().sum())
    if dup_count > 0:
        df = df[~df.index.duplicated(keep="last")]
        validation_report["duplicate_dates_removed"] = dup_count

    # 2. Drop rows with missing OHLCV values
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    before_na = len(df)
    df = df.dropna(subset=required_cols)
    validation_report["missing_values_dropped"] = before_na - len(df)

    # 3. Remove inconsistent rows (High < Low, negative prices, or negative volume)
    inconsistent_mask = (
        (df["High"] < df["Low"])
        | (df["Open"] <= 0)
        | (df["Close"] <= 0)
        | (df["Volume"] < 0)
    )
    inconsistent_count = int(inconsistent_mask.sum())
    if inconsistent_count > 0:
        df = df[~inconsistent_mask]
        validation_report["inconsistent_rows_removed"] = inconsistent_count

    # Convert to JSON-serializable list of dicts
    records = []
    for date_idx, row in df.iterrows():
        records.append({
            "date": date_idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    validation_report["total_rows_clean"] = len(records)
    return records, validation_report

def _df_to_clean_dict(df: pd.DataFrame, max_periods: int = 4) -> dict:
    """Safely converts a Yahoo Finance financial statement DataFrame to JSON."""
    if df is None or df.empty:
        return {}
    # Limit to most recent periods and replace NaN with None
    trimmed = df.iloc[:, :max_periods]
    result = {}
    for col in trimmed.columns:
        col_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        result[col_key] = {
            str(idx): (None if pd.isna(val) else float(val))
            for idx, val in trimmed[col].items()
        }
    return result

def get_full_market_data(symbol: str, market: str = "NASDAQ", period: str = "1 Year") -> dict:
    """
    Fetches historical OHLCV, company profile, financial statements,
    validation metrics, and source metadata for a given stock.
    """
    formatted_symbol = format_ticker_for_market(symbol, market)
    yf_period = PERIOD_MAP.get(period, "1y")
    retrieved_at = datetime.now(timezone.utc).isoformat()

    ticker = yf.Ticker(formatted_symbol)

    # 1. Historical OHLCV Data + Validation
    hist_df = ticker.history(period=yf_period)
    ohlcv_records, validation_report = validate_and_clean_ohlcv(hist_df)

    # 2. Company Profile
    info = ticker.info or {}
    profile = {
        "symbol": formatted_symbol,
        "company_name": info.get("longName") or info.get("shortName") or formatted_symbol,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "exchange": info.get("exchange"),
        "currency": info.get("currency", "USD"),
        "market_cap": info.get("marketCap"),
        "website": info.get("website"),
        "summary": info.get("longBusinessSummary"),
    }

    # 3. Financial Statements
    financials = {
        "income_statement": _df_to_clean_dict(ticker.financials),
        "balance_sheet": _df_to_clean_dict(ticker.balance_sheet),
        "cash_flow": _df_to_clean_dict(ticker.cashflow),
    }

    return {
        "metadata": {
            "requested_symbol": symbol.upper(),
            "resolved_symbol": formatted_symbol,
            "market": market.upper(),
            "period": period,
            "source": "Yahoo Finance (yfinance)",
            "source_url": f"https://finance.yahoo.com/quote/{formatted_symbol}",
            "retrieved_at": retrieved_at,
        },
        "validation": validation_report,
        "profile": profile,
        "ohlcv": ohlcv_records,
        "financials": financials,
    }