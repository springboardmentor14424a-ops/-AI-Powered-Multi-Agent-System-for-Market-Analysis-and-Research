import logging
import math
import re
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import Any, TypeVar

import yfinance as yf

from .schemas import (
    DataSourceInfo,
    MarketDataResponse,
    OHLCVBar,
    StockSearchResponse,
    StockSearchResult,
)

logger = logging.getLogger(__name__)
Result = TypeVar("Result")
DATA_PROVIDER = "Yahoo Finance via yfinance"
ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
ALLOWED_MARKETS = {"US", "NSE", "BSE"}
TICKER_PATTERN = re.compile(r"^[A-Za-z0-9.^=&_-]{1,30}$")


class YFinanceError(RuntimeError):
    pass


def _call_provider(action: str, operation: Callable[[], Result]) -> Result:
    try:
        return operation()
    except Exception as error:
        logger.exception("Yahoo Finance failed while %s", action)
        raise YFinanceError(f"Yahoo Finance could not {action}. Please try again later.") from error


def _source(ticker: str, retrieved_at: datetime) -> DataSourceInfo:
    return DataSourceInfo(
        provider=DATA_PROVIDER,
        url=f"https://finance.yahoo.com/quote/{ticker}/",
        retrieved_at=retrieved_at,
    )


def normalize_ticker(ticker: str, market: str) -> str:
    normalized_ticker = ticker.strip().upper()
    if not TICKER_PATTERN.fullmatch(normalized_ticker):
        raise ValueError("Enter a valid stock ticker symbol")
    if market not in ALLOWED_MARKETS:
        raise ValueError("Market must be US, NSE, or BSE")

    if market == "NSE":
        if normalized_ticker.endswith(".BO"):
            raise ValueError("A BSE ticker cannot be used with the NSE market")
        if not normalized_ticker.endswith(".NS"):
            normalized_ticker = f"{normalized_ticker}.NS"
    elif market == "BSE":
        if normalized_ticker.endswith(".NS"):
            raise ValueError("An NSE ticker cannot be used with the BSE market")
        if not normalized_ticker.endswith(".BO"):
            normalized_ticker = f"{normalized_ticker}.BO"
    elif normalized_ticker.endswith((".NS", ".BO")):
        raise ValueError("Select NSE or BSE for this ticker")

    return normalized_ticker


def _belongs_to_market(ticker: str, exchange: str | None, market: str) -> bool:
    symbol = ticker.upper()
    normalized_exchange = (exchange or "").upper()
    if market == "NSE":
        return symbol.endswith(".NS") or normalized_exchange in {"NSI", "NSE"}
    if market == "BSE":
        return symbol.endswith(".BO") or normalized_exchange in {"BSE", "BOM"}
    return not symbol.endswith((".NS", ".BO"))


def search_stocks(query: str, market: str = "US", limit: int = 8) -> StockSearchResponse:
    normalized_query = query.strip()
    if len(normalized_query) < 2:
        raise ValueError("Search query must contain at least two characters")
    if market not in ALLOWED_MARKETS:
        raise ValueError("Market must be US, NSE, or BSE")

    search = _call_provider(
        "search for stocks",
        lambda: yf.Search(
            normalized_query,
            max_results=limit * 4 if market != "US" else limit,
            news_count=0,
            lists_count=0,
        ),
    )
    results: list[StockSearchResult] = []
    seen_tickers: set[str] = set()
    for quote in search.quotes:
        ticker = quote.get("symbol")
        if (
            not ticker
            or ticker in seen_tickers
            or not _belongs_to_market(ticker, quote.get("exchange"), market)
        ):
            continue
        seen_tickers.add(ticker)
        results.append(
            StockSearchResult(
                ticker=ticker,
                name=quote.get("shortname") or quote.get("longname") or ticker,
                exchange=quote.get("exchange"),
                quote_type=quote.get("quoteType"),
            )
        )
        if len(results) >= limit:
            break

    return StockSearchResponse(
        results=results,
        market=market,
        source=DATA_PROVIDER,
        retrieved_at=datetime.now(timezone.utc),
    )


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, (str, bytes, bool)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    date_method = getattr(value, "date", None)
    if date_method:
        parsed = date_method()
        if isinstance(parsed, date):
            return parsed
    return None


def build_market_data(
    ticker: str,
    info: dict[str, Any],
    period: str,
    history: Any,
    market: str = "US",
) -> MarketDataResponse:
    if period not in ALLOWED_PERIODS:
        raise ValueError(f"Period must be one of: {', '.join(sorted(ALLOWED_PERIODS))}")
    if history is None or history.empty:
        raise YFinanceError(f"Yahoo Finance returned no historical price data for {ticker}.")

    warnings: list[str] = []
    duplicate_count = int(history.index.duplicated().sum())
    if duplicate_count:
        history = history[~history.index.duplicated(keep="last")]
        warnings.append(f"Removed {duplicate_count} duplicate price date(s).")

    bars: list[OHLCVBar] = []
    invalid_rows = 0
    missing_volume_rows = 0
    for index, row in history.sort_index().iterrows():
        day = _date(index)
        open_price = _number(row.get("Open"))
        high = _number(row.get("High"))
        low = _number(row.get("Low"))
        close = _number(row.get("Close"))
        if (
            day is None
            or open_price is None
            or high is None
            or low is None
            or close is None
            or low > high
            or low > min(open_price, close)
            or high < max(open_price, close)
        ):
            invalid_rows += 1
            continue

        volume_value = _number(row.get("Volume"))
        if volume_value is None:
            missing_volume_rows += 1
        elif volume_value < 0:
            invalid_rows += 1
            continue

        bars.append(
            OHLCVBar(
                date=day,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=int(volume_value) if volume_value is not None else None,
            )
        )

    if invalid_rows:
        warnings.append(f"Excluded {invalid_rows} invalid OHLCV row(s).")
    if missing_volume_rows:
        warnings.append(f"{missing_volume_rows} price row(s) had no volume value.")
    if not bars:
        raise YFinanceError(f"Yahoo Finance returned no valid historical price data for {ticker}.")

    retrieved_at = datetime.now(timezone.utc)
    return MarketDataResponse(
        ticker=ticker,
        market=market,
        company_name=info.get("shortName") or info.get("longName") or ticker,
        currency=info.get("currency"),
        exchange=info.get("exchangeName") or info.get("fullExchangeName"),
        period=period,
        prices=bars,
        warnings=warnings,
        source=_source(ticker, retrieved_at),
    )


def fetch_market_data(ticker: str, period: str = "1y", market: str = "US") -> MarketDataResponse:
    normalized_ticker = normalize_ticker(ticker, market)
    if period not in ALLOWED_PERIODS:
        raise ValueError(f"Period must be one of: {', '.join(sorted(ALLOWED_PERIODS))}")

    stock = yf.Ticker(normalized_ticker)
    info = _call_provider(
        f"retrieve company information for {normalized_ticker}",
        stock.get_info,
    )
    if not isinstance(info, dict):
        info = {}
    history = _call_provider(
        f"retrieve historical prices for {normalized_ticker}",
        lambda: stock.history(period=period, auto_adjust=False),
    )
    return build_market_data(normalized_ticker, info, period, history, market)
