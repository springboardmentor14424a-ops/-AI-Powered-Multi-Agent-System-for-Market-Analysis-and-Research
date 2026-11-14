"""Validated ticker list used for stock search and the watchlist.

This is a curated sample of well-known listings, not the full exchanges. To use a
live market-data provider later, replace `search_stocks` / `find_stock` only.

Ticker formats (as stored in this app):
  NSE        plain symbol            RELIANCE, TCS
  BSE        6-digit scrip code      500325 (Reliance), 532540 (TCS)
  NASDAQ/NYSE  plain symbol          AAPL, JPM
`provider_symbol()` converts to the Yahoo-Finance-style form many data
providers expect (RELIANCE.NS, 500325.BO, AAPL).
"""

# (market, ticker, company name)
_STOCKS: list[tuple[str, str, str]] = [
    # NASDAQ
    ("NASDAQ", "AAPL", "Apple Inc."),
    ("NASDAQ", "MSFT", "Microsoft Corporation"),
    ("NASDAQ", "GOOGL", "Alphabet Inc."),
    ("NASDAQ", "AMZN", "Amazon.com, Inc."),
    ("NASDAQ", "NVDA", "NVIDIA Corporation"),
    ("NASDAQ", "META", "Meta Platforms, Inc."),
    ("NASDAQ", "TSLA", "Tesla, Inc."),
    ("NASDAQ", "NFLX", "Netflix, Inc."),
    ("NASDAQ", "AMD", "Advanced Micro Devices, Inc."),
    ("NASDAQ", "INTC", "Intel Corporation"),
    ("NASDAQ", "ADBE", "Adobe Inc."),
    ("NASDAQ", "CSCO", "Cisco Systems, Inc."),
    ("NASDAQ", "PEP", "PepsiCo, Inc."),
    ("NASDAQ", "COST", "Costco Wholesale Corporation"),
    ("NASDAQ", "QCOM", "QUALCOMM Incorporated"),
    ("NASDAQ", "AVGO", "Broadcom Inc."),
    ("NASDAQ", "PYPL", "PayPal Holdings, Inc."),
    ("NASDAQ", "SBUX", "Starbucks Corporation"),
    # NYSE
    ("NYSE", "JPM", "JPMorgan Chase & Co."),
    ("NYSE", "V", "Visa Inc."),
    ("NYSE", "WMT", "Walmart Inc."),
    ("NYSE", "JNJ", "Johnson & Johnson"),
    ("NYSE", "XOM", "Exxon Mobil Corporation"),
    ("NYSE", "BAC", "Bank of America Corporation"),
    ("NYSE", "KO", "The Coca-Cola Company"),
    ("NYSE", "DIS", "The Walt Disney Company"),
    ("NYSE", "NKE", "NIKE, Inc."),
    ("NYSE", "MCD", "McDonald's Corporation"),
    ("NYSE", "BA", "The Boeing Company"),
    ("NYSE", "IBM", "International Business Machines Corporation"),
    ("NYSE", "ORCL", "Oracle Corporation"),
    ("NYSE", "T", "AT&T Inc."),
    ("NYSE", "PFE", "Pfizer Inc."),
    ("NYSE", "UBER", "Uber Technologies, Inc."),
    ("NYSE", "CRM", "Salesforce, Inc."),
    ("NYSE", "GS", "The Goldman Sachs Group, Inc."),
    # NSE
    ("NSE", "RELIANCE", "Reliance Industries Limited"),
    ("NSE", "TCS", "Tata Consultancy Services Limited"),
    ("NSE", "HDFCBANK", "HDFC Bank Limited"),
    ("NSE", "INFY", "Infosys Limited"),
    ("NSE", "ICICIBANK", "ICICI Bank Limited"),
    ("NSE", "SBIN", "State Bank of India"),
    ("NSE", "BHARTIARTL", "Bharti Airtel Limited"),
    ("NSE", "ITC", "ITC Limited"),
    ("NSE", "HINDUNILVR", "Hindustan Unilever Limited"),
    ("NSE", "LT", "Larsen & Toubro Limited"),
    ("NSE", "KOTAKBANK", "Kotak Mahindra Bank Limited"),
    ("NSE", "AXISBANK", "Axis Bank Limited"),
    ("NSE", "WIPRO", "Wipro Limited"),
    ("NSE", "HCLTECH", "HCL Technologies Limited"),
    ("NSE", "MARUTI", "Maruti Suzuki India Limited"),
    ("NSE", "SUNPHARMA", "Sun Pharmaceutical Industries Limited"),
    ("NSE", "ASIANPAINT", "Asian Paints Limited"),
    ("NSE", "BAJFINANCE", "Bajaj Finance Limited"),
    ("NSE", "TITAN", "Titan Company Limited"),
    ("NSE", "NTPC", "NTPC Limited"),
    ("NSE", "ONGC", "Oil and Natural Gas Corporation Limited"),
    ("NSE", "TATASTEEL", "Tata Steel Limited"),
    # BSE (scrip codes)
    ("BSE", "500325", "Reliance Industries Limited"),
    ("BSE", "532540", "Tata Consultancy Services Limited"),
    ("BSE", "500180", "HDFC Bank Limited"),
    ("BSE", "500209", "Infosys Limited"),
    ("BSE", "532174", "ICICI Bank Limited"),
    ("BSE", "500112", "State Bank of India"),
    ("BSE", "532454", "Bharti Airtel Limited"),
    ("BSE", "500875", "ITC Limited"),
    ("BSE", "500696", "Hindustan Unilever Limited"),
    ("BSE", "500510", "Larsen & Toubro Limited"),
]

_INDEX = {(m, t): n for m, t, n in _STOCKS}


# Approximate calendar days covered by each analysis period.
PERIOD_DAYS = {"1 month": 30, "3 months": 90, "6 months": 182, "1 year": 365, "5 years": 1825}


def provider_symbol(market: str, ticker: str) -> str:
    if market == "NSE":
        return f"{ticker}.NS"
    if market == "BSE":
        return f"{ticker}.BO"
    return ticker


def _as_dict(market: str, ticker: str, name: str) -> dict:
    return {
        "ticker": ticker,
        "company_name": name,
        "market": market,
        "provider_symbol": provider_symbol(market, ticker),
    }


def find_stock(market: str, ticker: str) -> dict | None:
    name = _INDEX.get((market, ticker.upper()))
    return _as_dict(market, ticker.upper(), name) if name else None


def search_stocks(query: str, market: str | None = None, limit: int = 10) -> list[dict]:
    """Case-insensitive search by ticker or company name, best matches first."""
    q = query.strip().lower()
    if not q:
        return []
    scored = []
    for m, t, n in _STOCKS:
        if market and m != market:
            continue
        tl, nl = t.lower(), n.lower()
        if tl == q:
            score = 0
        elif tl.startswith(q):
            score = 1
        elif nl.startswith(q):
            score = 2
        elif q in tl:
            score = 3
        elif q in nl:
            score = 4
        else:
            continue
        scored.append((score, n, m, t))
    scored.sort()
    return [_as_dict(m, t, n) for _, n, m, t in scored[:limit]]
