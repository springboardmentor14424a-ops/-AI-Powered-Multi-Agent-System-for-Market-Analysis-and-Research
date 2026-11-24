import math
import threading
import time

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone

import yfinance as yf

from app.constants import (
    SUPPORTED_MARKETS,
    SUPPORTED_PERIODS
)


# --------------------------------------------------
# MARKET DATA SERVICE
# --------------------------------------------------

DATA_PROVIDER = "Yahoo Finance"


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved or validated."""


PERIOD_MAP = {
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "5Y": "5y"
}

# --------------------------------------------------
# IN-MEMORY MARKET DATA CACHE
# --------------------------------------------------

PROFILE_CACHE_TTL = 6 * 60 * 60
HISTORY_CACHE_TTL = 15 * 60
FINANCIAL_STATEMENTS_CACHE_TTL = 6 * 60 * 60

MAX_CACHE_ENTRIES = 256

_market_data_cache = OrderedDict()

_cache_lock = threading.RLock()
_inflight_requests = {}


def clear_market_data_cache():
    """Clear all cached market data."""

    with _cache_lock:
        _market_data_cache.clear()


def _get_or_fetch_cached(cache_key, ttl, fetch_function):
    """
    Return cached data or fetch it once.

    Uses LRU eviction and prevents duplicate concurrent
    fetches for the same cache key.
    """

    while True:
        with _cache_lock:

            now = time.monotonic()

            cached = _market_data_cache.get(cache_key)

            if cached is not None:
                expires_at, cached_data = cached

                if now < expires_at:
                    _market_data_cache.move_to_end(cache_key)
                    return deepcopy(cached_data)

                del _market_data_cache[cache_key]

            request_event = _inflight_requests.get(cache_key)

            if request_event is None:
                request_event = threading.Event()
                _inflight_requests[cache_key] = request_event
                is_fetch_owner = True

            else:
                is_fetch_owner = False

        if is_fetch_owner:
            break

        request_event.wait()

    try:
        result = fetch_function()

        cached_result = deepcopy(result)

        with _cache_lock:

            _market_data_cache[cache_key] = (
                time.monotonic() + ttl,
                cached_result
            )

            _market_data_cache.move_to_end(cache_key)

            while len(_market_data_cache) > MAX_CACHE_ENTRIES:
                _market_data_cache.popitem(last=False)

        return deepcopy(cached_result)

    finally:
        with _cache_lock:
            event = _inflight_requests.pop(cache_key, None)

            if event is not None:
                event.set()


# --------------------------------------------------
# MARKET VALIDATION
# --------------------------------------------------

def normalize_market(market: str) -> str:
    normalized = market.strip().upper()

    if normalized not in SUPPORTED_MARKETS:
        raise ValueError(
            f"Unsupported market. Supported markets: "
            f"{', '.join(SUPPORTED_MARKETS)}"
        )

    return normalized


# --------------------------------------------------
# CONVERT STOCKPILOT TICKER TO YFINANCE SYMBOL
# --------------------------------------------------

def get_provider_symbol(ticker: str, market: str) -> str:
    normalized_ticker = ticker.strip().upper()
    normalized_market = normalize_market(market)

    if not normalized_ticker:
        raise ValueError("A valid stock ticker is required")

    if normalized_market == "NSE":
        if normalized_ticker.endswith(".BO"):
            raise ValueError(
                "BSE ticker cannot be used with NSE market"
            )

        return (
            normalized_ticker
            if normalized_ticker.endswith(".NS")
            else f"{normalized_ticker}.NS"
        )

    if normalized_market == "BSE":
        if normalized_ticker.endswith(".NS"):
            raise ValueError(
                "NSE ticker cannot be used with BSE market"
            )

        return (
            normalized_ticker
            if normalized_ticker.endswith(".BO")
            else f"{normalized_ticker}.BO"
        )

    if normalized_ticker.endswith((".NS", ".BO")):
        raise ValueError(
            "Indian exchange ticker cannot be used with a US market"
        )

    return normalized_ticker


# --------------------------------------------------
# SAFE NUMERIC CONVERSION
# --------------------------------------------------

def safe_number(value):
    try:
        if value is None or isinstance(value, bool):
            return None

        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (TypeError, ValueError, OverflowError):
        return None


# --------------------------------------------------
# FETCH COMPANY PROFILE
# --------------------------------------------------

def _fetch_stock_profile(ticker: str, market: str) -> dict:
    normalized_market = normalize_market(market)

    provider_symbol = get_provider_symbol(
        ticker,
        normalized_market
    )

    try:
        stock = yf.Ticker(provider_symbol)
        info = stock.info

        if not isinstance(info, dict) or not info:
            raise MarketDataError(
                "Company profile is unavailable"
            )

        company_name = (
            info.get("longName")
            or info.get("shortName")
        )

        if not company_name:
            raise MarketDataError(
                "Company information was not found"
            )

        employees_value = info.get("fullTimeEmployees")

        employees = (
            employees_value
            if isinstance(employees_value, int)
            and not isinstance(employees_value, bool)
            and employees_value >= 0
            else None
        )

        return {
            "ticker": ticker.strip().upper(),
            "provider_symbol": provider_symbol,
            "company_name": company_name,
            "market": normalized_market,
            "exchange": info.get("exchange"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get("longBusinessSummary"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "website": info.get("website"),
            "market_cap": safe_number(
                info.get("marketCap")
            ),
            "employees": employees,
            "data_provider": DATA_PROVIDER,
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except MarketDataError:
        raise

    except Exception as exc:
        raise MarketDataError(
            "Company profile is temporarily unavailable"
        ) from exc

def get_stock_profile(ticker: str, market: str) -> dict:
    normalized_market = normalize_market(market)
    normalized_ticker = ticker.strip().upper()

    provider_symbol = get_provider_symbol(
        normalized_ticker,
        normalized_market
    )

    cache_key = (
        "profile",
        provider_symbol,
        normalized_market
    )

    return _get_or_fetch_cached(
        cache_key,
        PROFILE_CACHE_TTL,
        lambda: _fetch_stock_profile(
            normalized_ticker,
            normalized_market
        )
    )


# --------------------------------------------------
# FETCH HISTORICAL OHLCV DATA
# --------------------------------------------------

def _fetch_stock_history(
    ticker: str,
    market: str,
    period: str
) -> dict:

    normalized_market = normalize_market(market)
    normalized_period = period.strip().upper()

    if normalized_period not in SUPPORTED_PERIODS:
        raise ValueError(
            f"Unsupported period. Supported periods: "
            f"{', '.join(SUPPORTED_PERIODS)}"
        )

    provider_symbol = get_provider_symbol(
        ticker,
        normalized_market
    )

    try:
        stock = yf.Ticker(provider_symbol)

        history = stock.history(
            period=PERIOD_MAP[normalized_period],
            interval="1d",
            auto_adjust=False,
            actions=False
        )

        if history is None or history.empty:
            raise MarketDataError(
                "Historical stock data is unavailable"
            )

        records = []

        invalid_rows = 0
        missing_values = 0
        adjusted_close_missing = 0
        invalid_timestamps = 0

        seen_timestamps = set()
        duplicate_rows = 0

        for timestamp, row in history.iterrows():

            # --------------------------------------
            # TIMESTAMP VALIDATION
            # --------------------------------------

            
            try:
                if timestamp is None or timestamp != timestamp:
                    raise ValueError("Missing or invalid timestamp")

                if not hasattr(timestamp, "isoformat"):
                    raise ValueError("Invalid timestamp")

                timestamp_string = timestamp.isoformat()

                if (
                    not timestamp_string
                    or timestamp_string.lower() in {"nat", "nan", "none"}
                ):
                    raise ValueError("Invalid timestamp")
                

            except (TypeError, ValueError, AttributeError):
                invalid_rows += 1
                invalid_timestamps += 1
                continue

            if timestamp_string in seen_timestamps:
                duplicate_rows += 1
                continue

            seen_timestamps.add(timestamp_string)

            # --------------------------------------
            # NUMERIC VALIDATION
            # --------------------------------------

            open_price = safe_number(row.get("Open"))
            high_price = safe_number(row.get("High"))
            low_price = safe_number(row.get("Low"))
            close_price = safe_number(row.get("Close"))

            adjusted_close = safe_number(
                row.get("Adj Close")
            )

            volume = safe_number(row.get("Volume"))

            required_values = [
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ]

            if any(value is None for value in required_values):
                missing_values += 1
                invalid_rows += 1
                continue

            # --------------------------------------
            # OHLC AND VOLUME VALIDATION
            # --------------------------------------

            if (
                open_price <= 0
                or high_price <= 0
                or low_price <= 0
                or close_price <= 0
                or high_price < low_price
                or high_price < max(open_price, close_price)
                or low_price > min(open_price, close_price)
                or volume < 0
                or not volume.is_integer()
            ):
                invalid_rows += 1
                continue

            # --------------------------------------
            # ADJUSTED CLOSE VALIDATION
            # --------------------------------------

            if adjusted_close is None:
                adjusted_close_missing += 1

            elif adjusted_close <= 0:
                adjusted_close = None
                adjusted_close_missing += 1

            # --------------------------------------
            # VALID RECORD
            # --------------------------------------

            records.append({
                "timestamp": timestamp_string,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "adjusted_close": adjusted_close,
                "volume": int(volume)
            })

        # ------------------------------------------
        # ENSURE USABLE HISTORICAL DATA
        # ------------------------------------------

        if not records:
            raise MarketDataError(
                "No valid historical stock records were found"
            )

        records.sort(
            key=lambda item: item["timestamp"]
        )

        # ------------------------------------------
        # RETRIEVE CURRENCY
        # ------------------------------------------

        currency = None

        try:
            currency = stock.fast_info.get("currency")
        except Exception:
            currency = None

        # ------------------------------------------
        # VALIDATION SUMMARY
        # ------------------------------------------

        validation = {
            "is_valid": (
                invalid_rows == 0
                and duplicate_rows == 0
            ),
            "valid_rows": len(records),
            "invalid_rows": invalid_rows,
            "missing_values": missing_values,
            "adjusted_close_missing": adjusted_close_missing,
            "invalid_timestamps": invalid_timestamps,
            "duplicate_rows": duplicate_rows
        }

        return {
            "ticker": ticker.strip().upper(),
            "provider_symbol": provider_symbol,
            "market": normalized_market,
            "period": normalized_period,
            "interval": "1d",
            "currency": currency,
            "records": records,
            "record_count": len(records),
            "validation": validation,
            "data_provider": DATA_PROVIDER,
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except MarketDataError:
        raise

    except Exception as exc:
        raise MarketDataError(
            "Historical stock data is temporarily unavailable"
        ) from exc

def get_stock_history(
    ticker: str,
    market: str,
    period: str
) -> dict:
    normalized_market = normalize_market(market)
    normalized_period = period.strip().upper()
    normalized_ticker = ticker.strip().upper()

    if normalized_period not in SUPPORTED_PERIODS:
        raise ValueError(
            f"Unsupported period. Supported periods: "
            f"{', '.join(SUPPORTED_PERIODS)}"
        )

    provider_symbol = get_provider_symbol(
        normalized_ticker,
        normalized_market
    )

    cache_key = (
        "history",
        provider_symbol,
        normalized_market,
        normalized_period
    )

    return _get_or_fetch_cached(
        cache_key,
        HISTORY_CACHE_TTL,
        lambda: _fetch_stock_history(
            normalized_ticker,
            normalized_market,
            normalized_period
        )
    )


# --------------------------------------------------
# FETCH FINANCIAL STATEMENTS
# --------------------------------------------------

def _fetch_stock_financial_statements(
    ticker: str,
    market: str
) -> dict:

    normalized_market = normalize_market(market)

    provider_symbol = get_provider_symbol(
        ticker,
        normalized_market
    )

    statement_sources = [
        ("income_statement", "annual", "income_stmt"),
        ("income_statement", "quarterly", "quarterly_income_stmt"),
        ("balance_sheet", "annual", "balance_sheet"),
        ("balance_sheet", "quarterly", "quarterly_balance_sheet"),
        ("cash_flow", "annual", "cashflow"),
        ("cash_flow", "quarterly", "quarterly_cashflow"),
    ]

    try:
        stock = yf.Ticker(provider_symbol)

        statements = []
        available_statements = []
        unavailable_statements = []

        failed_statement_requests = 0

        for statement_type, frequency, attribute in statement_sources:

            statement_name = f"{statement_type}_{frequency}"

            try:
                dataframe = getattr(stock, attribute)

                if dataframe is None or dataframe.empty:
                    unavailable_statements.append(statement_name)
                    continue

                periods = []

                for period_end in dataframe.columns:

                    try:
                        if period_end is None or period_end != period_end:
                            continue

                        if not hasattr(period_end, "isoformat"):
                            continue

                        period_string = period_end.isoformat()

                        if period_string.lower() in {"nat", "nan", "none"}:
                            continue

                    except (TypeError, ValueError, AttributeError):
                        continue

                    values = {}

                    for line_item, row in dataframe.iterrows():
                        values[str(line_item)] = safe_number(
                            row.get(period_end)
                        )

                    periods.append({
                        "period_end": period_string,
                        "values": values
                    })

                if not periods:
                    unavailable_statements.append(statement_name)
                    continue

                periods.sort(
                    key=lambda item: item["period_end"],
                    reverse=True
                )

                statements.append({
                    "statement_type": statement_type,
                    "frequency": frequency,
                    "periods": periods
                })

                available_statements.append(statement_name)

            except Exception:
                # One unavailable statement must not prevent
                # the remaining statements from being retrieved.
                failed_statement_requests += 1
                unavailable_statements.append(statement_name)

        if failed_statement_requests == len(statement_sources):
            raise MarketDataError(
                "Financial statements are temporarily unavailable"
            )
        
        currency = None

        try:
            currency = stock.fast_info.get("currency")
        except Exception:
            pass

        return {
            "ticker": ticker.strip().upper(),
            "provider_symbol": provider_symbol,
            "market": normalized_market,
            "currency": currency,
            "statements": statements,
            "available_statements": available_statements,
            "unavailable_statements": unavailable_statements,
            "data_provider": DATA_PROVIDER,
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except Exception as exc:
        raise MarketDataError(
            "Financial statements are temporarily unavailable"
        ) from exc


# --------------------------------------------------
# GET FINANCIAL STATEMENTS WITH CACHE
# --------------------------------------------------

def get_stock_financial_statements(
    ticker: str,
    market: str
) -> dict:

    normalized_market = normalize_market(market)
    normalized_ticker = ticker.strip().upper()

    provider_symbol = get_provider_symbol(
        normalized_ticker,
        normalized_market
    )

    cache_key = (
        "financial_statements",
        provider_symbol,
        normalized_market
    )

    return _get_or_fetch_cached(
        cache_key,
        FINANCIAL_STATEMENTS_CACHE_TTL,
        lambda: _fetch_stock_financial_statements(
            normalized_ticker,
            normalized_market
        )
    )
