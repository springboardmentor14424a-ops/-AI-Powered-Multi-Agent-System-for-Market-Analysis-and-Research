"""
Market Data Collection Service
Implements Module 2: Stock Search and Market Data Collection
- Company search with exchange isolation across NSE, BSE, NASDAQ, NYSE
- Historical OHLCV stock price collection with custom start/end dates and intervals (1d, 1wk, 1mo)
- Company profiles and real financial statements (Income Statement, Balance Sheet, Cash Flow)
- Rigorous data validation engine (Null checks, duplicate dates, negative values, OHLC rule violations)
- Source traceability and retrieval timestamps
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import re

from app.services.market_data import DEFAULT_TICKERS, search_companies_by_market

# Catalog of all supported securities across exchanges with country metadata
EXCHANGE_COMPANIES = {
    "NSE": [dict(c, country="India") for c in DEFAULT_TICKERS if c["market"] == "NSE"],
    "BSE": [dict(c, country="India") for c in DEFAULT_TICKERS if c["market"] == "BSE"],
    "NASDAQ": [dict(c, country="United States") for c in DEFAULT_TICKERS if c["market"] == "NASDAQ"],
    "NYSE": [dict(c, country="United States") for c in DEFAULT_TICKERS if c["market"] == "NYSE"]
}

MARKET_SUFFIX = {
    "NSE": ".NS",
    "BSE": ".BO",
    "NASDAQ": "",
    "NYSE": "",
}

VALID_INTERVALS = ["1d", "1wk", "1mo"]

def search_market_companies(market: str, query: str = "") -> List[Dict[str, Any]]:
    """
    Search for companies within a specific stock exchange.
    Ensures strict exchange isolation and displays company name, ticker, exchange, and country.
    Never returns companies belonging to unselected exchange markets.
    If no matches are found, returns an empty list. Never substitutes fake companies.
    """
    return search_companies_by_market(market, query)

def format_ticker_for_market(ticker: str, market: str) -> str:
    """Appends appropriate exchange suffix for Yahoo Finance query."""
    clean = ticker.strip().upper()
    suffix = MARKET_SUFFIX.get(market.upper(), "")
    if suffix and not clean.endswith(suffix):
        return f"{clean}{suffix}"
    return clean

def validate_ohlcv_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs comprehensive data validation on retrieved OHLCV records:
    1. Missing or NULL values (date, open, high, low, close, volume)
    2. Duplicate trading dates
    3. Negative stock prices or trading volumes
    4. Invalid OHLC relationships (High >= Open, Close, Low; Low <= Open, Close)
    5. Inconsistent or malformed records
    """
    total_records = len(records)
    if total_records == 0:
        return {
            "status": "FAILED",
            "is_valid": False,
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "null_values_count": 0,
            "duplicate_dates_count": 0,
            "negative_values_count": 0,
            "ohlc_rule_violations_count": 0,
            "warnings": ["Dataset contains 0 trading sessions."],
            "checks": {
                "null_values_check": "FAILED",
                "duplicate_dates_check": "PASSED",
                "negative_values_check": "PASSED",
                "ohlc_relationship_check": "PASSED",
                "data_consistency_check": "FAILED"
            },
            "validated_records": []
        }

    null_count = 0
    negative_count = 0
    ohlc_violations = 0
    seen_dates = set()
    duplicate_dates = []
    warnings = []
    validated_records = []

    for idx, r in enumerate(records):
        record_flags = []
        d = r.get("date")
        op = r.get("open")
        hi = r.get("high")
        lo = r.get("low")
        cl = r.get("close")
        vo = r.get("volume")

        # 1. Null / Missing Values Check
        if None in [d, op, hi, lo, cl, vo] or any(np.isnan(v) for v in [op, hi, lo, cl, vo] if isinstance(v, (int, float))):
            null_count += 1
            record_flags.append("Missing/Null values")

        # 2. Duplicate Trading Dates Check
        if d in seen_dates:
            duplicate_dates.append(d)
            record_flags.append(f"Duplicate date: {d}")
        else:
            if d:
                seen_dates.add(d)

        # 3. Negative Stock Prices or Trading Volumes Check
        if any(isinstance(v, (int, float)) and v < 0 for v in [op, hi, lo, cl, vo]):
            negative_count += 1
            record_flags.append("Negative price or volume value")

        # 4. Invalid OHLC Relationships Check
        # High must be >= Open, Close, Low
        # Low must be <= Open, Close
        if all(isinstance(v, (int, float)) for v in [op, hi, lo, cl]):
            if not (hi >= op and hi >= cl and hi >= lo):
                ohlc_violations += 1
                record_flags.append("Invalid OHLC: High is lower than Open, Close, or Low")
            if not (lo <= op and lo <= cl):
                ohlc_violations += 1
                record_flags.append("Invalid OHLC: Low is higher than Open or Close")

        validated_records.append({
            **r,
            "is_valid": len(record_flags) == 0,
            "validation_flags": record_flags
        })

    if null_count > 0:
        warnings.append(f"Detected {null_count} record(s) containing missing or null fields.")
    if len(duplicate_dates) > 0:
        warnings.append(f"Detected {len(duplicate_dates)} duplicate trading date(s): {', '.join(duplicate_dates[:3])}.")
    if negative_count > 0:
        warnings.append(f"Detected {negative_count} record(s) with anomalous negative price or volume.")
    if ohlc_violations > 0:
        warnings.append(f"Detected {ohlc_violations} record(s) violating OHLC relationships (High >= O/C/L, Low <= O/C).")

    invalid_records = sum(1 for r in validated_records if not r["is_valid"])
    valid_records = total_records - invalid_records

    # Determine status
    if total_records > 0 and invalid_records == 0:
        status = "PASSED"
    elif valid_records > 0 and invalid_records <= (total_records * 0.05):
        status = "WARNINGS"
    else:
        status = "FAILED"

    checks = {
        "null_values_check": "PASSED" if null_count == 0 else "WARNINGS",
        "duplicate_dates_check": "PASSED" if len(duplicate_dates) == 0 else "WARNINGS",
        "negative_values_check": "PASSED" if negative_count == 0 else "FAILED",
        "ohlc_relationship_check": "PASSED" if ohlc_violations == 0 else "WARNINGS",
        "data_consistency_check": "PASSED" if status in ["PASSED", "WARNINGS"] else "FAILED"
    }

    return {
        "status": status,
        "is_valid": status in ["PASSED", "WARNINGS"],
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "null_values_count": null_count,
        "duplicate_dates_count": len(duplicate_dates),
        "negative_values_count": negative_count,
        "ohlc_rule_violations_count": ohlc_violations,
        "warnings": warnings,
        "checks": checks,
        "validated_records": validated_records
    }

def clean_financial_df(df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
    """Converts a pandas financial DataFrame into clean JSON-serializable rows."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    try:
        # Transpose so rows are dates or periods, or keep line items as rows
        # Standard yfinance DataFrame has line items as index and date Timestamps as columns
        result = []
        date_cols = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c) for c in df.columns]

        for metric_name, row in df.iterrows():
            metric_data = {
                "metric": str(metric_name),
            }
            for original_col, date_str in zip(df.columns, date_cols):
                val = row[original_col]
                if pd.isna(val) or val is None or np.isnan(val) if isinstance(val, (int, float)) else False:
                    metric_data[date_str] = None
                else:
                    metric_data[date_str] = float(val) if isinstance(val, (int, float, np.number)) else str(val)
            result.append(metric_data)
        return result
    except Exception:
        return []

def fetch_market_data_collection(
    ticker: str,
    market: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d"
) -> Dict[str, Any]:
    """
    Primary data acquisition workflow for Module 2:
    - Queries historical OHLCV data for custom date ranges and interval
    - Runs validation engine
    - Retrieves company profile and financial statements
    - Attaches data source traceability and timestamps
    """
    clean_ticker = ticker.strip().upper()
    market_upper = market.strip().upper()
    yf_symbol = format_ticker_for_market(clean_ticker, market_upper)
    safe_interval = interval if interval in VALID_INTERVALS else "1d"
    country = "India" if market_upper in ["NSE", "BSE"] else "United States"

    # Default date range to past 1 year if not specified
    now = datetime.now()
    if not end_date:
        end_date = now.strftime("%Y-%m-%d")
    if not start_date:
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    retrieval_utc = datetime.now(timezone.utc)
    trace_id = str(uuid.uuid4())

    t = yf.Ticker(yf_symbol)

    # 1. Fetch Historical OHLCV Data
    raw_ohlcv_records = []
    fetch_error = None
    try:
        hist = t.history(start=start_date, end=end_date, interval=safe_interval)
        if hist.empty:
            # Fallback to period query if custom range returned empty
            hist = t.history(period="1y", interval=safe_interval)

        if not hist.empty:
            hist_len = len(hist)
            for idx in range(hist_len):
                row = hist.iloc[idx]
                dt_str = hist.index[idx].strftime("%Y-%m-%d")
                prev_close = float(hist.iloc[idx - 1]["Close"]) if idx > 0 else float(row["Open"])
                close_val = round(float(row["Close"]), 2)
                chg = round(close_val - prev_close, 2)
                chg_pct = round((chg / prev_close) * 100, 2) if prev_close else 0.0

                raw_ohlcv_records.append({
                    "date": dt_str,
                    "open": round(float(row["Open"]), 2) if not pd.isna(row["Open"]) else None,
                    "high": round(float(row["High"]), 2) if not pd.isna(row["High"]) else None,
                    "low": round(float(row["Low"]), 2) if not pd.isna(row["Low"]) else None,
                    "close": close_val if not pd.isna(row["Close"]) else None,
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                    "change": chg,
                    "change_pct": chg_pct,
                })
    except Exception as e:
        fetch_error = str(e)

    # 2. Run Data Validation Engine
    validation_report = validate_ohlcv_dataset(raw_ohlcv_records)

    # 3. Retrieve Company Profile
    info = {}
    try:
        info = t.info or {}
    except Exception:
        pass

    # Extract CEO & officers
    officers = []
    for off in info.get("companyOfficers", [])[:3]:
        officers.append({
            "name": off.get("name", "N/A"),
            "title": off.get("title", "Executive"),
            "pay": off.get("totalPay")
        })

    ceo_name = None
    for off in officers:
        if "ceo" in (off.get("title") or "").lower() or "chief executive" in (off.get("title") or "").lower():
            ceo_name = off.get("name")
            break
    if not ceo_name and officers:
        ceo_name = officers[0].get("name")

    currency = info.get("currency") or ("INR" if market_upper in ["NSE", "BSE"] else "USD")

    company_profile = {
        "company_name": info.get("longName") or info.get("shortName") or clean_ticker,
        "ticker": clean_ticker,
        "formatted_symbol": yf_symbol,
        "market": market_upper,
        "country": country,
        "currency": currency,
        "sector": info.get("sector") or "N/A",
        "industry": info.get("industry") or "N/A",
        "market_cap": info.get("marketCap"),
        "ceo": ceo_name or "N/A",
        "headquarters": {
            "address": info.get("address1") or "N/A",
            "city": info.get("city") or "N/A",
            "state": info.get("state") or "N/A",
            "country": info.get("country") or country,
        },
        "website": info.get("website") or "N/A",
        "description": info.get("longBusinessSummary") or "Detailed profile not published by exchange.",
        "employees": info.get("fullTimeEmployees"),
        "trailing_pe": round(float(info["trailingPE"]), 2) if info.get("trailingPE") else None,
        "forward_pe": round(float(info["forwardPE"]), 2) if info.get("forwardPE") else None,
        "dividend_yield": round(float(info["dividendYield"]) * 100, 2) if info.get("dividendYield") else None,
        "beta": round(float(info["beta"]), 2) if info.get("beta") else None,
        "officers": officers
    }

    # 4. Retrieve Financial Statements
    income_statement = []
    balance_sheet = []
    cash_flow = []

    try:
        income_statement = clean_financial_df(t.financials)
    except Exception:
        pass

    try:
        balance_sheet = clean_financial_df(t.balance_sheet)
    except Exception:
        pass

    try:
        cash_flow = clean_financial_df(t.cashflow)
    except Exception:
        pass

    financial_statements = {
        "has_financials": bool(income_statement or balance_sheet or cash_flow),
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
        "cash_flow_statement": cash_flow,
    }

    return {
        "trace_id": trace_id,
        "ticker": clean_ticker,
        "company_name": company_profile["company_name"],
        "market": market_upper,
        "country": country,
        "start_date": start_date,
        "end_date": end_date,
        "interval": safe_interval,
        "data_source": "Yahoo Finance (yfinance API)",
        "retrieved_at_utc": retrieval_utc.isoformat(),
        "retrieved_at_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "record_count": len(raw_ohlcv_records),
        "fetch_error": fetch_error,
        "validation": validation_report,
        "ohlcv_records": validation_report["validated_records"],
        "company_profile": company_profile,
        "financial_statements": financial_statements
    }
