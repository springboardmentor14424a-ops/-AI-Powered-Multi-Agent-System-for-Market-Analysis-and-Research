"""Validated ticker list used for search (Module 1).

The guide allows "a suitable market-data API or a validated ticker list".
This curated list keeps Module 1 self-contained; swap `search_stocks` /
`find_stock` for a real provider (yfinance, Alpha Vantage, ...) later.
"""

CATALOG: list[dict] = [
    # NSE
    {"ticker": "RELIANCE", "name": "Reliance Industries Ltd", "market": "NSE"},
    {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "NSE"},
    {"ticker": "INFY", "name": "Infosys Ltd", "market": "NSE"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank Ltd", "market": "NSE"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank Ltd", "market": "NSE"},
    {"ticker": "SBIN", "name": "State Bank of India", "market": "NSE"},
    {"ticker": "ITC", "name": "ITC Ltd", "market": "NSE"},
    {"ticker": "WIPRO", "name": "Wipro Ltd", "market": "NSE"},
    {"ticker": "BHARTIARTL", "name": "Bharti Airtel Ltd", "market": "NSE"},
    {"ticker": "LT", "name": "Larsen & Toubro Ltd", "market": "NSE"},
    {"ticker": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "market": "NSE"},
    {"ticker": "TATAMOTORS", "name": "Tata Motors Ltd", "market": "NSE"},
    # BSE (same companies, listed on BSE)
    {"ticker": "RELIANCE", "name": "Reliance Industries Ltd", "market": "BSE"},
    {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "BSE"},
    {"ticker": "INFY", "name": "Infosys Ltd", "market": "BSE"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank Ltd", "market": "BSE"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank Ltd", "market": "BSE"},
    {"ticker": "SBIN", "name": "State Bank of India", "market": "BSE"},
    {"ticker": "ITC", "name": "ITC Ltd", "market": "BSE"},
    {"ticker": "WIPRO", "name": "Wipro Ltd", "market": "BSE"},
    # NASDAQ
    {"ticker": "AAPL", "name": "Apple Inc.", "market": "NASDAQ"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "market": "NASDAQ"},
    {"ticker": "AMZN", "name": "Amazon.com, Inc.", "market": "NASDAQ"},
    {"ticker": "TSLA", "name": "Tesla, Inc.", "market": "NASDAQ"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ"},
    {"ticker": "META", "name": "Meta Platforms, Inc.", "market": "NASDAQ"},
    {"ticker": "NFLX", "name": "Netflix, Inc.", "market": "NASDAQ"},
    {"ticker": "AMD", "name": "Advanced Micro Devices, Inc.", "market": "NASDAQ"},
    {"ticker": "INTC", "name": "Intel Corporation", "market": "NASDAQ"},
    # NYSE
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "market": "NYSE"},
    {"ticker": "KO", "name": "The Coca-Cola Company", "market": "NYSE"},
    {"ticker": "DIS", "name": "The Walt Disney Company", "market": "NYSE"},
    {"ticker": "BA", "name": "The Boeing Company", "market": "NYSE"},
    {"ticker": "WMT", "name": "Walmart Inc.", "market": "NYSE"},
    {"ticker": "V", "name": "Visa Inc.", "market": "NYSE"},
    {"ticker": "XOM", "name": "Exxon Mobil Corporation", "market": "NYSE"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "market": "NYSE"},
    {"ticker": "PG", "name": "The Procter & Gamble Company", "market": "NYSE"},
    {"ticker": "NKE", "name": "NIKE, Inc.", "market": "NYSE"},
]

# Ticker suffix the data provider (e.g. Yahoo Finance) expects per market.
PROVIDER_SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}


def provider_symbol(ticker: str, market: str) -> str:
    """e.g. ('TCS','NSE') -> 'TCS.NS' ; ('AAPL','NASDAQ') -> 'AAPL'"""
    return f"{ticker}{PROVIDER_SUFFIX.get(market, '')}"


def find_stock(ticker: str, market: str) -> dict | None:
    ticker = ticker.strip().upper()
    for s in CATALOG:
        if s["ticker"] == ticker and s["market"] == market:
            return s
    return None


def search_stocks(query: str, market: str | None = None, limit: int = 10) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    results = []
    for s in CATALOG:
        if market and s["market"] != market:
            continue
        if q in s["ticker"].lower() or q in s["name"].lower():
            results.append({**s, "provider_symbol": provider_symbol(s["ticker"], s["market"])})
    # exact/prefix ticker matches first
    results.sort(key=lambda s: (not s["ticker"].lower().startswith(q), s["ticker"]))
    return results[:limit]
