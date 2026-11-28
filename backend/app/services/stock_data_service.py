
import pandas as pd
import yfinance as yf

from datetime import datetime, timezone


# ==========================================================
# CONFIGURATION
# ==========================================================

DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"
DATA_SOURCE = "Yahoo Finance"

ALLOWED_MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"]

ALLOWED_PERIODS = ["1mo", "3mo", "6mo", "1y", "5y"]


# ==========================================================
# VALIDATE STOCK SYMBOL
# ==========================================================

def validate_symbol(symbol: str) -> str:

    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Stock symbol is required.")

    symbol = symbol.strip().upper()

    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-^="

    if any(char not in allowed for char in symbol):
        raise ValueError("Invalid stock symbol.")

    return symbol


# ==========================================================
# PREPARE SYMBOL ACCORDING TO MARKET
# ==========================================================

def prepare_market_symbol(ticker: str, market: str) -> str:

    ticker = validate_symbol(ticker)

    market = market.strip().upper()

    if market not in ALLOWED_MARKETS:
        raise ValueError("Unsupported stock market.")

    if "." in ticker or ticker.startswith("^"):
        return ticker

    if market == "NSE":
        return ticker + ".NS"

    if market == "BSE":
        return ticker + ".BO"

    return ticker


# ==========================================================
# FETCH STOCK DATA
# ==========================================================

def fetch_stock_data(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL
) -> pd.DataFrame:

    symbol = validate_symbol(symbol)

    if period not in ALLOWED_PERIODS:
        raise ValueError("Unsupported analysis period.")

    try:
        stock = yf.Ticker(symbol)

        data = stock.history(
            period=period,
            interval=interval,
            auto_adjust=False
        )

    except Exception as error:
        raise RuntimeError(
            f"Stock data download failed: {error}"
        )

    if data is None or data.empty:
        raise ValueError(f"No data found for {symbol}")

    return data


# ==========================================================
# VALIDATE DATA
# ==========================================================

def validate_stock_data(data: pd.DataFrame) -> pd.DataFrame:

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    if data is None or data.empty:
        raise ValueError("Stock data is empty.")

    for column in required_columns:
        if column not in data.columns:
            raise ValueError(f"Missing column: {column}")

    data = data.copy()

    data = data[~data.index.duplicated(keep="last")]
    data = data.sort_index()

    for column in required_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data = data.dropna(subset=required_columns)

    if data.empty:
        raise ValueError("No valid stock records available.")

    if (data["Close"] <= 0).any():
        raise ValueError("Invalid closing prices found.")

    if (data["Open"] <= 0).any():
        raise ValueError("Invalid opening prices found.")

    if (data["High"] <= 0).any():
        raise ValueError("Invalid high prices found.")

    if (data["Low"] <= 0).any():
        raise ValueError("Invalid low prices found.")

    if (data["Volume"] < 0).any():
        raise ValueError("Invalid volume values found.")

    if (data["High"] < data["Low"]).any():
        raise ValueError("Inconsistent high and low prices found.")

    if (
        data["High"] <
        data[["Open", "Close"]].max(axis=1)
    ).any():
        raise ValueError("High price is inconsistent with OHLC data.")

    if (
        data["Low"] >
        data[["Open", "Close"]].min(axis=1)
    ).any():
        raise ValueError("Low price is inconsistent with OHLC data.")

    return data


# ==========================================================
# DAILY RETURNS
# ==========================================================

def calculate_returns(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    data["Daily_Change"] = data["Close"].diff()

    data["Daily_Return_Percent"] = (
        data["Close"].pct_change() * 100
    )

    return data


# ==========================================================
# MOVING AVERAGES
# ==========================================================

def calculate_moving_averages(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    close = data["Close"]

    data["MA5"] = close.rolling(5).mean()
    data["MA20"] = close.rolling(20).mean()
    data["MA50"] = close.rolling(50).mean()
    data["MA200"] = close.rolling(200).mean()

    return data


# ==========================================================
# RSI
# ==========================================================

def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14
) -> pd.DataFrame:

    data = data.copy()

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    data["RSI"] = 100 - (100 / (1 + rs))

    data.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI"
    ] = 100

    data.loc[
        (avg_gain == 0) & (avg_loss > 0),
        "RSI"
    ] = 0

    return data


# ==========================================================
# MACD
# ==========================================================

def calculate_macd(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    close = data["Close"]

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    data["MACD"] = ema12 - ema26

    data["MACD_Signal"] = data["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    data["MACD_Histogram"] = (
        data["MACD"] - data["MACD_Signal"]
    )

    return data


# ==========================================================
# MOVING AVERAGE CROSSOVER
# ==========================================================

def detect_ma_crossover(data: pd.DataFrame) -> str:

    valid = data.dropna(subset=["MA50", "MA200"])

    if len(valid) < 2:
        return "Insufficient data for crossover analysis"

    previous = valid.iloc[-2]
    latest = valid.iloc[-1]

    if (
        previous["MA50"] <= previous["MA200"]
        and latest["MA50"] > latest["MA200"]
    ):
        return "Golden Cross detected"

    if (
        previous["MA50"] >= previous["MA200"]
        and latest["MA50"] < latest["MA200"]
    ):
        return "Death Cross detected"

    if latest["MA50"] > latest["MA200"]:
        return "MA50 above MA200 - Uptrend condition"

    if latest["MA50"] < latest["MA200"]:
        return "MA50 below MA200 - Downtrend condition"

    return "MA50 and MA200 are equal"


# ==========================================================
# STOCK SUMMARY
# ==========================================================

def generate_stock_summary(
    symbol: str,
    data: pd.DataFrame
) -> dict:

    latest = data.iloc[-1]

    previous_close = (
        data["Close"].iloc[-2]
        if len(data) >= 2
        else None
    )

    change = (
        float(latest["Close"]) - float(previous_close)
        if previous_close is not None
        else None
    )

    change_percent = (
        (change / float(previous_close)) * 100
        if previous_close is not None and previous_close != 0
        else None
    )

    def safe_value(column):

        value = latest[column]

        return (
            round(float(value), 2)
            if pd.notna(value)
            else None
        )

    return {
        "symbol": symbol,
        "latest_date": str(data.index[-1]),
        "open": safe_value("Open"),
        "high": safe_value("High"),
        "low": safe_value("Low"),
        "close": safe_value("Close"),
        "daily_change": (
            round(change, 2)
            if change is not None else None
        ),
        "daily_change_percent": (
            round(change_percent, 2)
            if change_percent is not None else None
        ),
        "volume": int(latest["Volume"]),
        "ma5": safe_value("MA5"),
        "ma20": safe_value("MA20"),
        "ma50": safe_value("MA50"),
        "ma200": safe_value("MA200"),
        "rsi": safe_value("RSI"),
        "macd": safe_value("MACD"),
        "macd_signal": safe_value("MACD_Signal"),
        "macd_histogram": safe_value("MACD_Histogram"),
        "ma_crossover": detect_ma_crossover(data)
    }


# ==========================================================
# STOCK ANALYSIS
# ==========================================================

def get_stock_analysis(
    symbol: str,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL
) -> dict:

    symbol = validate_symbol(symbol)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    data = fetch_stock_data(
        symbol,
        period,
        interval
    )

    data = validate_stock_data(data)

    data = calculate_returns(data)
    data = calculate_moving_averages(data)
    data = calculate_rsi(data)
    data = calculate_macd(data)

    summary = generate_stock_summary(
        symbol,
        data
    )

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "summary": summary,
        "historical_data": data,
        "metadata": {
            "source": DATA_SOURCE,
            "retrieved_at": retrieved_at,
            "records_count": len(data)
        }
    }


# ==========================================================
# COMPANY SEARCH
# ==========================================================

def search_companies(
    query: str,
    market: str,
    max_results: int = 10
) -> list:

    if not query or not query.strip():
        raise ValueError("Search query is required.")

    market = market.strip().upper()

    if market not in ALLOWED_MARKETS:
        raise ValueError("Unsupported stock market.")

    try:
        results = yf.Search(
            query.strip(),
            max_results=max_results
        )

        quotes = getattr(results, "quotes", []) or []

        companies = []

        for item in quotes:

            symbol = item.get("symbol", "")

            if not symbol:
                continue

            exchange = str(
                item.get("exchange", "")
            ).upper()

            if market == "NSE" and not symbol.endswith(".NS"):
                continue

            if market == "BSE" and not symbol.endswith(".BO"):
                continue

            if market == "NASDAQ" and exchange != "NMS":
                continue

            if market == "NYSE" and exchange != "NYQ":
                continue

            companies.append({
                "symbol": symbol,
                "name": (
                    item.get("longname")
                    or item.get("shortname")
                    or symbol
                ),
                "exchange": exchange,
                "market": market
            })

        return companies[:max_results]

    except Exception as error:
        raise RuntimeError(
            f"Company search failed: {error}"
        )


# ==========================================================
# COMPANY PROFILE
# ==========================================================

def get_company_profile(symbol: str) -> dict:

    symbol = validate_symbol(symbol)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    try:
        stock = yf.Ticker(symbol)

        profile = stock.get_info()

        if not profile:
            raise ValueError(
                f"No company profile found for {symbol}"
            )

        fields = [
            "longName",
            "shortName",
            "symbol",
            "sector",
            "industry",
            "country",
            "website",
            "longBusinessSummary",
            "currency",
            "marketCap",
            "fullTimeEmployees",
            "exchange"
        ]

        result = {
            key: profile.get(key)
            for key in fields
        }

        result["metadata"] = {
            "source": DATA_SOURCE,
            "retrieved_at": retrieved_at
        }

        return result

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Company profile retrieval failed: {error}"
        )


# ==========================================================
# FINANCIAL STATEMENTS
# ==========================================================

def get_financial_statements(symbol: str) -> dict:

    symbol = validate_symbol(symbol)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    try:
        stock = yf.Ticker(symbol)

        return {
            "symbol": symbol,
            "income_statement": stock.financials,
            "balance_sheet": stock.balance_sheet,
            "cash_flow": stock.cashflow,
            "metadata": {
                "source": DATA_SOURCE,
                "retrieved_at": retrieved_at
            }
        }

    except Exception as error:
        raise RuntimeError(
            f"Financial statement retrieval failed: {error}"
        )
