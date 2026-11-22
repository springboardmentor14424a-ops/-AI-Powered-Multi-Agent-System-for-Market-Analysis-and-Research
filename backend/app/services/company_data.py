
"""
company_data.py
===============
Retrieves company profiles and financial statements from Yahoo Finance.

Supports both NSE (.NS) and BSE (.BO) listed stocks.
All responses include a retrieval timestamp and data source identifier.
No financial values are invented or silently altered.
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timezone
from typing import Literal


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

DATA_SOURCE = "Yahoo Finance (yfinance)"


def _now_utc() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_yf_ticker(ticker: str, market: str) -> str:
    """
    Normalise the ticker symbol for Yahoo Finance.
    - NSE stocks: append .NS unless already suffixed
    - BSE stocks: append .BO unless already suffixed
    - NASDAQ & NYSE stocks: use bare ticker symbol without suffix
    Already-suffixed tickers pass through or are normalised as appropriate.
    """
    sym = ticker.strip().upper()
    mkt = market.strip().upper()

    if mkt == "NSE":
        if sym.endswith(".BO"):
            sym = sym[:-3]
        if not sym.endswith(".NS"):
            sym = sym + ".NS"

    elif mkt == "BSE":
        if sym.endswith(".NS"):
            sym = sym[:-3]
        if not sym.endswith(".BO"):
            sym = sym + ".BO"

    elif mkt in ("NASDAQ", "NYSE"):
        if sym.endswith(".NS") or sym.endswith(".BO"):
            sym = sym[:-3]
        sym = sym.split(".")[0]

    return sym


def _safe_float(value) -> float | None:
    """Convert a value to float, returning None if conversion fails or NaN."""
    if value is None:
        return None
    try:
        f = float(value)
        return None if (f != f) else f   # NaN check: NaN != NaN
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> int | None:
    """Convert a value to int, returning None if conversion fails."""
    if value is None:
        return None
    try:
        f = float(value)
        if f != f:          # NaN
            return None
        return int(f)
    except (TypeError, ValueError):
        return None


def _serialize_dataframe(df) -> dict[str, dict[str, float | None]] | None:
    """
    Convert a yfinance financial-statement DataFrame into a plain dict.

    Shape:
        {
          "2026-03-31": {"Total Revenue": 283248007577.0, "EBITDA": null, ...},
          "2025-03-31": {...},
          ...
        }

    Rules:
    - Column headers (dates) are formatted as YYYY-MM-DD strings.
    - Row index labels (line items) are kept as-is.
    - NaN values are replaced with None so the JSON is clean.
    - Original values are never altered.
    """
    if df is None or df.empty:
        return None

    result: dict = {}

    for col in df.columns:
        date_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        result[date_key] = {}

        for idx in df.index:
            raw = df.loc[idx, col]

            # numpy types → Python native
            if isinstance(raw, (np.floating, float)):
                val = None if np.isnan(raw) else float(raw)
            elif isinstance(raw, (np.integer, int)):
                val = int(raw)
            else:
                val = None

            result[date_key][str(idx)] = val

    return result


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_statement(
    data: dict[str, dict[str, float | None]],
    statement_type: str
) -> list[str]:
    """
    Run validation checks on a serialised financial statement.
    Returns a deduplicated list of clear warning strings.

    Checks performed:
    1. Duplicate reporting dates
    2. Invalid / unparseable date strings
    3. Fully empty reporting periods
    4. Genuinely missing important financial metrics (without false alarms for optional metrics)
    """
    warnings: list[str] = []
    seen: set[str] = set()

    def add_warning(msg: str) -> None:
        if msg not in seen:
            seen.add(msg)
            warnings.append(msg)

    if not data:
        return warnings

    dates = list(data.keys())

    # 1. Duplicate dates check
    if len(dates) != len(set(dates)):
        duplicates = sorted(list(set(d for d in dates if dates.count(d) > 1)))
        add_warning(
            f"Duplicate reporting dates detected: {duplicates}"
        )

    # 2. Invalid date format check
    for d in dates:
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            add_warning(f"Invalid date format in reporting period: '{d}'")

    # 3. Core important metrics per statement (primary name, [provider candidate keys])
    # Warn only when NO candidate key has a non-null value for that period.
    core_metrics = {
        "income": [
            ("Total Revenue", ["Total Revenue", "Operating Revenue"]),
            ("Operating Income", ["Operating Income", "EBIT"]),
            ("Net Income", ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"]),
        ],
        "balance_sheet": [
            ("Total Assets", ["Total Assets"]),
            ("Total Liabilities", ["Total Liabilities Net Minority Interest", "Total Non Current Liabilities Net Minority Interest", "Current Liabilities"]),
            ("Stockholders Equity", ["Common Stock Equity", "Stockholders Equity", "Total Equity Gross Minority Interest"]),
        ],
        "cashflow": [
            ("Operating Cash Flow", ["Operating Cash Flow"]),
            ("Capital Expenditure", ["Capital Expenditure", "Capital Expenditure Reported"]),
            ("Free Cash Flow", ["Free Cash Flow"]),
        ],
    }

    # 4. Period inspection
    for period, rows in data.items():
        # Check if period is completely empty
        non_null_vals = [v for v in rows.values() if v is not None]
        if not non_null_vals:
            add_warning(f"All financial metrics are unavailable for reporting date {period}")
            continue

        # Check for genuinely missing core important metrics
        for metric_name, candidates in core_metrics.get(statement_type, []):
            has_valid = any(rows.get(c) is not None for c in candidates)
            if not has_valid:
                add_warning(
                    f"Important metric '{metric_name}' is unavailable for reporting date {period}"
                )

    return warnings


def _validate_profile(profile: dict) -> list[str]:
    """
    Validate a company profile dict (using mapped field names).
    Returns a list of warning strings.
    """
    warnings: list[str] = []

    expected_fields = [
        "company_name", "industry", "sector", "description",
        "website", "market_cap", "country", "currency",
    ]

    for field in expected_fields:
        if not profile.get(field):
            warnings.append(f"Profile field '{field}' is missing or null")

    return warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_company_profile(ticker: str, market: str) -> dict:
    """
    Retrieve company profile information for a given stock.

    Parameters
    ----------
    ticker : str
        The stock symbol (e.g. 'TCS', 'TCS.NS', 'TCS.BO').
    market : str
        'NSE' or 'BSE'.

    Returns
    -------
    dict with keys:
        success        : bool
        message        : str (error description when success=False)
        ticker         : str  (cleaned symbol passed to Yahoo Finance)
        market         : str
        retrieved_at   : str  (UTC ISO-8601 timestamp)
        data_source    : str
        profile        : dict | None
        validation_warnings : list[str]
    """
    retrieved_at = _now_utc()
    yf_ticker = _build_yf_ticker(ticker, market)

    try:
        stock = yf.Ticker(yf_ticker)
        info: dict = stock.info
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to contact data provider: {exc}",
            "ticker": yf_ticker,
            "market": market.upper(),
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "profile": None,
            "validation_warnings": [],
        }

    # yfinance returns a 1-key dict when the symbol is invalid
    if len(info) <= 1 or not info.get("longName"):
        return {
            "success": False,
            "message": f"No company profile found for '{yf_ticker}'. "
                       "The symbol may be invalid or delisted.",
            "ticker": yf_ticker,
            "market": market.upper(),
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "profile": None,
            "validation_warnings": [
                f"Symbol '{yf_ticker}' returned no profile data"
            ],
        }

    profile = {
        # Identity
        "company_name":   info.get("longName") or info.get("shortName"),
        "short_name":     info.get("shortName"),
        "ticker_symbol":  info.get("symbol", yf_ticker),
        "exchange":       info.get("fullExchangeName") or info.get("exchange"),
        "market":         market.upper(),
        "country":        info.get("country"),
        "currency":       info.get("currency") or info.get("financialCurrency"),

        # Classification
        "industry":       info.get("industry"),
        "sector":         info.get("sector"),

        # Description & web
        "description":    info.get("longBusinessSummary"),
        "website":        info.get("website") or info.get("irWebsite"),
        "employees":      _safe_int(info.get("fullTimeEmployees")),

        # Market data
        "market_cap":         _safe_float(info.get("marketCap")),
        "current_price":      _safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        "previous_close":     _safe_float(info.get("previousClose") or info.get("regularMarketPreviousClose")),
        "fifty_two_week_high": _safe_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low":  _safe_float(info.get("fiftyTwoWeekLow")),
        "beta":               _safe_float(info.get("beta")),
        "dividend_yield":     _safe_float(info.get("dividendYield")),

        # Valuation ratios
        "trailing_pe":    _safe_float(info.get("trailingPE")),
        "forward_pe":     _safe_float(info.get("forwardPE")),
        "price_to_book":  _safe_float(info.get("priceToBook")),

        # Financials summary
        "total_revenue":      _safe_float(info.get("totalRevenue")),
        "gross_profits":      _safe_float(info.get("grossProfits")),
        "ebitda":             _safe_float(info.get("ebitda")),
        "net_income":         _safe_float(info.get("netIncomeToCommon")),
        "total_debt":         _safe_float(info.get("totalDebt")),
        "total_cash":         _safe_float(info.get("totalCash")),
        "return_on_equity":   _safe_float(info.get("returnOnEquity")),
        "return_on_assets":   _safe_float(info.get("returnOnAssets")),
        "profit_margins":     _safe_float(info.get("profitMargins")),
        "book_value":         _safe_float(info.get("bookValue")),
    }

    validation_warnings = _validate_profile(profile)

    return {
        "success": True,
        "message": "Company profile retrieved successfully",
        "ticker": yf_ticker,
        "market": market.upper(),
        "retrieved_at": retrieved_at,
        "data_source": DATA_SOURCE,
        "profile": profile,
        "validation_warnings": validation_warnings,
    }


def get_financial_statements(
    ticker: str,
    market: str,
    statement: Literal["income", "balance_sheet", "cashflow"],
    frequency: Literal["annual", "quarterly"] = "annual",
) -> dict:
    """
    Retrieve a financial statement for a given stock.

    Parameters
    ----------
    ticker      : str   – stock symbol
    market      : str   – 'NSE' or 'BSE'
    statement   : str   – 'income' | 'balance_sheet' | 'cashflow'
    frequency   : str   – 'annual' | 'quarterly'

    Returns
    -------
    dict with keys:
        success              : bool
        message              : str
        ticker               : str
        market               : str
        statement            : str
        frequency            : str
        retrieved_at         : str
        data_source          : str
        reporting_periods    : list[str]  (sorted descending)
        data                 : dict | None  ({date: {line_item: value}})
        validation_warnings  : list[str]
    """
    retrieved_at = _now_utc()
    yf_ticker = _build_yf_ticker(ticker, market)

    allowed_statements = ("income", "balance_sheet", "cashflow")
    allowed_frequencies = ("annual", "quarterly")

    if statement not in allowed_statements:
        return {
            "success": False,
            "message": f"Invalid statement type '{statement}'. "
                       f"Choose from: {allowed_statements}",
            "ticker": yf_ticker,
            "market": market.upper(),
            "statement": statement,
            "frequency": frequency,
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "reporting_periods": [],
            "data": None,
            "validation_warnings": [],
        }

    if frequency not in allowed_frequencies:
        return {
            "success": False,
            "message": f"Invalid frequency '{frequency}'. "
                       f"Choose 'annual' or 'quarterly'.",
            "ticker": yf_ticker,
            "market": market.upper(),
            "statement": statement,
            "frequency": frequency,
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "reporting_periods": [],
            "data": None,
            "validation_warnings": [],
        }

    try:
        stock = yf.Ticker(yf_ticker)

        # Verify symbol exists (1-key dict means invalid ticker)
        if len(stock.info) <= 1:
            return {
                "success": False,
                "message": f"Symbol '{yf_ticker}' not found. "
                           "It may be invalid or delisted.",
                "ticker": yf_ticker,
                "market": market.upper(),
                "statement": statement,
                "frequency": frequency,
                "retrieved_at": retrieved_at,
                "data_source": DATA_SOURCE,
                "reporting_periods": [],
                "data": None,
                "validation_warnings": [
                    f"Symbol '{yf_ticker}' returned no data"
                ],
            }

        # Map request to the correct DataFrame attribute
        attr_map = {
            ("income",       "annual"):    "income_stmt",
            ("income",       "quarterly"): "quarterly_income_stmt",
            ("balance_sheet","annual"):    "balance_sheet",
            ("balance_sheet","quarterly"): "quarterly_balance_sheet",
            ("cashflow",     "annual"):    "cashflow",
            ("cashflow",     "quarterly"): "quarterly_cashflow",
        }

        df = getattr(stock, attr_map[(statement, frequency)], None)

    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to retrieve {statement} from data provider: {exc}",
            "ticker": yf_ticker,
            "market": market.upper(),
            "statement": statement,
            "frequency": frequency,
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "reporting_periods": [],
            "data": None,
            "validation_warnings": [],
        }

    if df is None or df.empty:
        return {
            "success": False,
            "message": f"No {frequency} {statement} data available for '{yf_ticker}'.",
            "ticker": yf_ticker,
            "market": market.upper(),
            "statement": statement,
            "frequency": frequency,
            "retrieved_at": retrieved_at,
            "data_source": DATA_SOURCE,
            "reporting_periods": [],
            "data": None,
            "validation_warnings": [
                f"{frequency.capitalize()} {statement} is empty for '{yf_ticker}'"
            ],
        }

    serialised = _serialize_dataframe(df)
    reporting_periods = sorted(serialised.keys(), reverse=True) if serialised else []
    validation_warnings = _validate_statement(serialised, statement)

    return {
        "success": True,
        "message": f"{frequency.capitalize()} {statement} retrieved successfully",
        "ticker": yf_ticker,
        "market": market.upper(),
        "statement": statement,
        "frequency": frequency,
        "retrieved_at": retrieved_at,
        "data_source": DATA_SOURCE,
        "reporting_periods": reporting_periods,
        "data": serialised,
        "validation_warnings": validation_warnings,
    }
