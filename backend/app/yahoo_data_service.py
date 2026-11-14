
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent

STOCKS_DIR = BASE_DIR / "data" / "yahoo_dataset" / "stocks"

METADATA_FILE = (
    BASE_DIR / "data" / "yahoo_dataset" / "symbols_valid_meta.csv"
)


def get_stock_list():
    """Return available companies and their ticker symbols."""

    metadata = pd.read_csv(METADATA_FILE)

    metadata = metadata[["Symbol", "Security Name", "Listing Exchange"]]

    metadata = metadata.dropna(subset=["Symbol"])

    return metadata.to_dict(orient="records")


def get_stock_data(ticker, analysis_period="3 Months"):
    """Load historical stock data for a selected ticker."""

    ticker = ticker.strip().upper()

    # Prevent invalid filenames and path traversal
    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("Invalid stock ticker")

    file_path = STOCKS_DIR / f"{ticker}.csv"

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Stock data not available for ticker {ticker}"
        )

    df = pd.read_csv(file_path)

    required_columns = [
        "Date", "Open", "High", "Low",
        "Close", "Adj Close", "Volume"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df = df.dropna(subset=["Date", "Close"])

    df = df.sort_values("Date").reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid historical stock records found")

    # Calculate period relative to the latest available dataset date.
    period_months = {
        "1 Month": 1,
        "3 Months": 3,
        "6 Months": 6,
        "1 Year": 12,
        "5 Years": 60
    }

    if analysis_period not in period_months:
        raise ValueError("Unsupported analysis period")

    latest_date = df["Date"].max()

    start_date = (
        latest_date - pd.DateOffset(
            months=period_months[analysis_period]
        )
    )

    filtered_df = df[df["Date"] >= start_date].copy()

    if filtered_df.empty:
        raise ValueError("No records found for selected period")

    first_record = filtered_df.iloc[0]
    last_record = filtered_df.iloc[-1]

    starting_price = float(first_record["Close"])
    ending_price = float(last_record["Close"])

    price_change = ending_price - starting_price

    percentage_change = (
        (price_change / starting_price) * 100
        if starting_price != 0 else 0
    )

    return {
        "ticker": ticker,
        "analysis_period": analysis_period,
        "data_start_date": first_record["Date"].strftime("%Y-%m-%d"),
        "data_end_date": last_record["Date"].strftime("%Y-%m-%d"),
        "records_count": len(filtered_df),
        "starting_price": round(starting_price, 2),
        "ending_price": round(ending_price, 2),
        "highest_price": round(float(filtered_df["High"].max()), 2),
        "lowest_price": round(float(filtered_df["Low"].min()), 2),
        "average_price": round(float(filtered_df["Close"].mean()), 2),
        "average_volume": int(filtered_df["Volume"].mean()),
        "price_change": round(price_change, 2),
        "percentage_change": round(percentage_change, 2)
    }


def search_stocks(search_text, limit=10):
    search_text = search_text.strip().upper()

    if not search_text:
        return []

    if len(search_text) > 50:
        raise ValueError("Search text is too long")

    metadata = pd.read_csv(METADATA_FILE)

    metadata = metadata[
        ["Symbol", "Security Name"]
    ].dropna()

    metadata["Symbol"] = metadata["Symbol"].astype(str).str.upper()
    metadata["Security Name"] = metadata["Security Name"].astype(str)

    matches = metadata[
        metadata["Symbol"].str.contains(
            search_text,
            regex=False
        )
        |
        metadata["Security Name"].str.upper().str.contains(
            search_text,
            regex=False
        )
    ]

    results = []

    for _, row in matches.iterrows():
        symbol = row["Symbol"]

        # Only show stocks that have a corresponding historical CSV.
        if (STOCKS_DIR / f"{symbol}.csv").is_file():
            results.append({
                "symbol": symbol,
                "company_name": row["Security Name"]
            })

        if len(results) >= limit:
            break

    return results


def get_stock_by_ticker(ticker):
    ticker = ticker.strip().upper()

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        return None

    metadata = pd.read_csv(METADATA_FILE)

    metadata["Symbol"] = metadata["Symbol"].astype(str).str.upper()

    matches = metadata[metadata["Symbol"] == ticker]

    if matches.empty:
        return None

    csv_path = STOCKS_DIR / f"{ticker}.csv"

    if not csv_path.is_file():
        return None

    return {
        "symbol": ticker,
        "company_name": str(matches.iloc[0]["Security Name"])
    }


def validate_stock_for_market(ticker, market):
    ticker = ticker.strip().upper()
    market = market.strip().upper()

    supported_markets = {"NSE", "BSE", "NASDAQ", "NYSE"}

    if market not in supported_markets:
        raise ValueError("Unsupported stock market.")

    # Validate market-specific ticker format
    if market == "NSE" and not ticker.endswith(".NS"):
        raise ValueError(
            "For NSE stocks, use the Yahoo Finance .NS suffix. "
            "Example: RELIANCE.NS"
        )

    if market == "BSE" and not ticker.endswith(".BO"):
        raise ValueError(
            "For BSE stocks, use the Yahoo Finance .BO suffix. "
            "Example: RELIANCE.BO"
        )

    if market in {"NASDAQ", "NYSE"} and (
        ticker.endswith(".NS") or ticker.endswith(".BO")
    ):
        raise ValueError(
            "Use an unsuffixed ticker for NASDAQ or NYSE."
        )

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("Invalid stock ticker format.")

    # Check that the local historical CSV exists
    file_path = STOCKS_DIR / f"{ticker}.csv"

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Historical data for {ticker} is not available "
            f"in the local dataset."
        )

    # For US stocks, verify the listing exchange using metadata.
    if market in {"NASDAQ", "NYSE"}:
        metadata = pd.read_csv(METADATA_FILE)

        metadata["Symbol"] = (
            metadata["Symbol"].astype(str).str.upper()
        )

        matching = metadata[
            metadata["Symbol"] == ticker
        ]

        if matching.empty:
            raise ValueError(
                f"{ticker} is not present in the stock metadata."
            )

        # Common exchange codes in the supplied symbol metadata:
        # Q = NASDAQ, N = NYSE.
        exchange_code = str(
            matching.iloc[0]["Listing Exchange"]
        ).strip().upper()

        exchange_map = {
            "Q": "NASDAQ",
            "N": "NYSE"
        }

        actual_market = exchange_map.get(exchange_code)

        if actual_market != market:
            raise ValueError(
                f"{ticker} is not listed on {market} "
                f"according to the available metadata."
            )

    return True
