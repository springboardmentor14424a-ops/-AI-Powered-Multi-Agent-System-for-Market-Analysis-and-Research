
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

STOCKS_DIR = (
    BASE_DIR / "data" / "yahoo_dataset" / "stocks"
)

METADATA_FILE = (
    BASE_DIR / "data" / "yahoo_dataset" / "symbols_valid_meta.csv"
)

SUPPORTED_PERIODS = {
    "1 Month": 1,
    "3 Months": 3,
    "6 Months": 6,
    "1 Year": 12,
    "5 Years": 60,
}


def load_metadata():
    """Load and validate company metadata."""

    if not METADATA_FILE.is_file():
        raise FileNotFoundError(
            "Yahoo Finance metadata file was not found."
        )

    metadata = pd.read_csv(METADATA_FILE)

    required_columns = [
        "Symbol",
        "Security Name",
        "Listing Exchange"
    ]

    missing = set(required_columns) - set(metadata.columns)

    if missing:
        raise ValueError(
            f"Missing metadata columns: {missing}"
        )

    metadata = metadata.dropna(
        subset=["Symbol", "Security Name"]
    ).copy()

    metadata["Symbol"] = (
        metadata["Symbol"].astype(str).str.strip().str.upper()
    )

    metadata["Security Name"] = (
        metadata["Security Name"].astype(str).str.strip()
    )

    return metadata


def search_stocks(search_text, limit=15):
    """
    Search companies using ticker symbol or company name.
    Only return companies with an available stock CSV.
    """

    search_text = str(search_text).strip()

    if not search_text:
        return []

    if len(search_text) > 50:
        raise ValueError("Search text is too long.")

    if limit < 1 or limit > 50:
        raise ValueError("Invalid search result limit.")

    metadata = load_metadata()

    query = search_text.upper()

    symbol_matches = metadata[
        metadata["Symbol"].str.contains(
            query, regex=False, na=False
        )
    ]

    name_matches = metadata[
        metadata["Security Name"].str.upper().str.contains(
            query, regex=False, na=False
        )
    ]

    # Exact ticker matches should appear first.
    exact_matches = metadata[
        metadata["Symbol"] == query
    ]

    matches = pd.concat(
        [exact_matches, symbol_matches, name_matches]
    ).drop_duplicates(subset=["Symbol"])

    results = []

    for _, row in matches.iterrows():

        ticker = row["Symbol"]

        csv_path = STOCKS_DIR / f"{ticker}.csv"

        if not csv_path.is_file():
            continue

        results.append({
            "symbol": ticker,
            "company_name": row["Security Name"],
            "listing_exchange": str(
                row["Listing Exchange"]
            )
        })

        if len(results) >= limit:
            break

    return results


def get_stock_data(ticker, analysis_period="3 Months"):
    """
    Collect historical market data from the local Yahoo dataset.
    """

    ticker = str(ticker).strip().upper()

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("Invalid stock ticker.")

    if analysis_period not in SUPPORTED_PERIODS:
        raise ValueError("Unsupported analysis period.")

    file_path = STOCKS_DIR / f"{ticker}.csv"

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Historical data not available for {ticker}."
        )

    df = pd.read_csv(file_path)

    required_columns = [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing stock CSV columns: {missing}"
        )

    df["Date"] = pd.to_datetime(
        df["Date"], errors="coerce"
    )

    numeric_columns = [
        "Open", "High", "Low", "Close",
        "Adj Close", "Volume"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    df = df.dropna(
        subset=["Date", "Open", "High", "Low", "Close", "Volume"]
    )

    df = df.sort_values("Date").reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid historical stock records found.")

    # Calculate period relative to the latest available dataset date.
    months = SUPPORTED_PERIODS[analysis_period]

    latest_date = df["Date"].max()

    start_date = latest_date - pd.DateOffset(
        months=months
    )

    filtered_df = df[
        df["Date"] >= start_date
    ].copy()

    if filtered_df.empty:
        raise ValueError(
            "No historical records available for this period."
        )

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

        "data_start_date": first_record["Date"].strftime(
            "%Y-%m-%d"
        ),

        "data_end_date": last_record["Date"].strftime(
            "%Y-%m-%d"
        ),

        "records_count": int(len(filtered_df)),

        "starting_price": round(starting_price, 2),
        "ending_price": round(ending_price, 2),

        "highest_price": round(
            float(filtered_df["High"].max()), 2
        ),

        "lowest_price": round(
            float(filtered_df["Low"].min()), 2
        ),

        "average_price": round(
            float(filtered_df["Close"].mean()), 2
        ),

        "average_volume": int(
            filtered_df["Volume"].mean()
        ),

        "price_change": round(price_change, 2),

        "percentage_change": round(
            percentage_change, 2
        ),

        "historical_data": [
            {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            }
            for _, row in filtered_df.iterrows()
        ]
    }


def get_stock_list(limit=100):
    """Return available stocks from the local dataset."""

    metadata = load_metadata()
    results = []

    for _, row in metadata.iterrows():
        ticker = row["Symbol"]
        csv_path = STOCKS_DIR / f"{ticker}.csv"

        if csv_path.is_file():
            results.append({
                "symbol": ticker,
                "company_name": row["Security Name"],
                "listing_exchange": str(row["Listing Exchange"])
            })

        if len(results) >= limit:
            break

    return results


def get_stock_by_ticker(ticker):
    """Find a stock using its exact ticker symbol."""

    ticker = str(ticker).strip().upper()

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("Invalid stock ticker.")

    metadata = load_metadata()

    matches = metadata[metadata["Symbol"] == ticker]

    if matches.empty:
        raise ValueError(f"Stock {ticker} was not found.")

    row = matches.iloc[0]

    csv_path = STOCKS_DIR / f"{ticker}.csv"

    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Historical data not available for {ticker}."
        )

    return {
        "symbol": ticker,
        "stock_ticker": ticker,
        "company_name": row["Security Name"],
        "listing_exchange": str(row["Listing Exchange"])
    }


def validate_stock_for_market(ticker, market):
    """Validate ticker and check that it belongs to the requested market."""

    ticker = str(ticker).strip().upper()
    market = str(market).strip().upper()

    supported_markets = {"NSE", "BSE", "NASDAQ", "NYSE"}

    if market not in supported_markets:
        raise ValueError("Unsupported stock market.")

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("Invalid stock ticker.")

    if market == "NSE" and not ticker.endswith(".NS"):
        raise ValueError("NSE tickers must end with .NS.")

    if market == "BSE" and not ticker.endswith(".BO"):
        raise ValueError("BSE tickers must end with .BO.")

    if market in {"NASDAQ", "NYSE"} and (
        ticker.endswith(".NS") or ticker.endswith(".BO")
    ):
        raise ValueError("Invalid ticker for US market.")

    stock = get_stock_by_ticker(ticker)

    if market in {"NASDAQ", "NYSE"}:
        exchange = stock["listing_exchange"].strip().upper()

        expected_exchange = {
            "NASDAQ": "Q",
            "NYSE": "N"
        }

        if exchange != expected_exchange[market]:
            raise ValueError(
                f"{ticker} does not belong to {market}."
            )

    return True
