"""
Market Data Service
Provides dynamic stock market data and historical datasets via Yahoo Finance (yfinance API).
Supports NASDAQ, NYSE, NSE (India), and BSE (India) as required by Module 1 specification.
"""

import yfinance as yf
from typing import Optional, Dict, Any, List

PERIOD_MAP = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
}

MARKET_SUFFIX = {
    "NSE": ".NS",
    "BSE": ".BO",
    "NASDAQ": "",
    "NYSE": "",
}

# Universe of well-known stocks for fast autocomplete across all 4 markets
DEFAULT_TICKERS = [
    # NSE – National Stock Exchange of India
    {"ticker": "TATAMOTORS", "name": "Tata Motors Limited", "market": "NSE"},
    {"ticker": "TATASTEEL", "name": "Tata Steel Limited", "market": "NSE"},
    {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "NSE"},
    {"ticker": "TATAPOWER", "name": "Tata Power Company Ltd", "market": "NSE"},
    {"ticker": "TATACONSUM", "name": "Tata Consumer Products Ltd", "market": "NSE"},
    {"ticker": "TATACHEM", "name": "Tata Chemicals Ltd", "market": "NSE"},
    {"ticker": "TATACOMM", "name": "Tata Communications Ltd", "market": "NSE"},
    {"ticker": "TATAELXSI", "name": "Tata Elxsi Ltd", "market": "NSE"},
    {"ticker": "TITAN", "name": "Titan Company Limited", "market": "NSE"},
    {"ticker": "RELIANCE", "name": "Reliance Industries Limited", "market": "NSE"},
    {"ticker": "INFY", "name": "Infosys Limited", "market": "NSE"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank Limited", "market": "NSE"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank Limited", "market": "NSE"},
    {"ticker": "SBIN", "name": "State Bank of India", "market": "NSE"},
    {"ticker": "WIPRO", "name": "Wipro Limited", "market": "NSE"},
    {"ticker": "BHARTIARTL", "name": "Bharti Airtel Limited", "market": "NSE"},
    {"ticker": "ITC", "name": "ITC Limited", "market": "NSE"},
    {"ticker": "LT", "name": "Larsen & Toubro Limited", "market": "NSE"},
    {"ticker": "HINDUNILVR", "name": "Hindustan Unilever Limited", "market": "NSE"},
    {"ticker": "BAJFINANCE", "name": "Bajaj Finance Limited", "market": "NSE"},
    {"ticker": "MARUTI", "name": "Maruti Suzuki India Limited", "market": "NSE"},
    {"ticker": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "market": "NSE"},
    {"ticker": "AXISBANK", "name": "Axis Bank Limited", "market": "NSE"},
    {"ticker": "KOTAKBANK", "name": "Kotak Mahindra Bank Limited", "market": "NSE"},
    {"ticker": "M&M", "name": "Mahindra & Mahindra Limited", "market": "NSE"},
    {"ticker": "NTPC", "name": "NTPC Limited", "market": "NSE"},
    {"ticker": "ONGC", "name": "Oil and Natural Gas Corporation", "market": "NSE"},
    {"ticker": "POWERGRID", "name": "Power Grid Corporation of India", "market": "NSE"},
    {"ticker": "ULTRACEMCO", "name": "UltraTech Cement Limited", "market": "NSE"},
    {"ticker": "ADANIENT", "name": "Adani Enterprises Limited", "market": "NSE"},
    {"ticker": "ADANIPORTS", "name": "Adani Ports and SEZ Ltd", "market": "NSE"},
    {"ticker": "ASIANPAINT", "name": "Asian Paints Limited", "market": "NSE"},
    {"ticker": "COALINDIA", "name": "Coal India Limited", "market": "NSE"},
    {"ticker": "BPCL", "name": "Bharat Petroleum Corporation Ltd", "market": "NSE"},
    {"ticker": "CIPLA", "name": "Cipla Limited", "market": "NSE"},
    {"ticker": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd", "market": "NSE"},
    {"ticker": "EICHERMOT", "name": "Eicher Motors Limited", "market": "NSE"},
    {"ticker": "GRASIM", "name": "Grasim Industries Limited", "market": "NSE"},
    {"ticker": "HCLTECH", "name": "HCL Technologies Limited", "market": "NSE"},
    {"ticker": "HINDALCO", "name": "Hindalco Industries Limited", "market": "NSE"},
    {"ticker": "HEROMOTOCO", "name": "Hero MotoCorp Limited", "market": "NSE"},
    {"ticker": "INDUSINDBK", "name": "IndusInd Bank Limited", "market": "NSE"},
    {"ticker": "JSWSTEEL", "name": "JSW Steel Limited", "market": "NSE"},
    {"ticker": "TECHM", "name": "Tech Mahindra Limited", "market": "NSE"},
    {"ticker": "NESTLEIND", "name": "Nestle India Limited", "market": "NSE"},
    {"ticker": "BRITANNIA", "name": "Britannia Industries Limited", "market": "NSE"},
    {"ticker": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "market": "NSE"},
    {"ticker": "DIVISLAB", "name": "Divi's Laboratories Limited", "market": "NSE"},
    {"ticker": "BAJAJFINSV", "name": "Bajaj Finserv Limited", "market": "NSE"},
    {"ticker": "BEL", "name": "Bharat Electronics Limited", "market": "NSE"},
    {"ticker": "TRENT", "name": "Trent Limited", "market": "NSE"},
    {"ticker": "SHRIRAMFIN", "name": "Shriram Finance Limited", "market": "NSE"},
    {"ticker": "ZOMATO", "name": "Zomato Limited", "market": "NSE"},
    {"ticker": "JIOFIN", "name": "Jio Financial Services Ltd", "market": "NSE"},
    {"ticker": "VBL", "name": "Varun Beverages Limited", "market": "NSE"},

    # BSE – Bombay Stock Exchange, India
    {"ticker": "TATAMOTORS", "name": "Tata Motors Limited", "market": "BSE"},
    {"ticker": "TATASTEEL", "name": "Tata Steel Limited", "market": "BSE"},
    {"ticker": "TCS", "name": "Tata Consultancy Services Ltd", "market": "BSE"},
    {"ticker": "TATAPOWER", "name": "Tata Power Company Ltd", "market": "BSE"},
    {"ticker": "TATACONSUM", "name": "Tata Consumer Products Ltd", "market": "BSE"},
    {"ticker": "TATACHEM", "name": "Tata Chemicals Ltd", "market": "BSE"},
    {"ticker": "TATACOMM", "name": "Tata Communications Ltd", "market": "BSE"},
    {"ticker": "TATAELXSI", "name": "Tata Elxsi Ltd", "market": "BSE"},
    {"ticker": "TITAN", "name": "Titan Company Limited", "market": "BSE"},
    {"ticker": "RELIANCE", "name": "Reliance Industries Limited", "market": "BSE"},
    {"ticker": "INFY", "name": "Infosys Limited", "market": "BSE"},
    {"ticker": "SBIN", "name": "State Bank of India", "market": "BSE"},
    {"ticker": "WIPRO", "name": "Wipro Limited", "market": "BSE"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank Limited", "market": "BSE"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank Limited", "market": "BSE"},
    {"ticker": "ITC", "name": "ITC Limited", "market": "BSE"},
    {"ticker": "BHARTIARTL", "name": "Bharti Airtel Limited", "market": "BSE"},
    {"ticker": "LT", "name": "Larsen & Toubro Limited", "market": "BSE"},
    {"ticker": "HINDUNILVR", "name": "Hindustan Unilever Limited", "market": "BSE"},
    {"ticker": "BAJFINANCE", "name": "Bajaj Finance Limited", "market": "BSE"},
    {"ticker": "MARUTI", "name": "Maruti Suzuki India Limited", "market": "BSE"},
    {"ticker": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "market": "BSE"},
    {"ticker": "AXISBANK", "name": "Axis Bank Limited", "market": "BSE"},
    {"ticker": "KOTAKBANK", "name": "Kotak Mahindra Bank Limited", "market": "BSE"},
    {"ticker": "M&M", "name": "Mahindra & Mahindra Limited", "market": "BSE"},
    {"ticker": "NTPC", "name": "NTPC Limited", "market": "BSE"},
    {"ticker": "ONGC", "name": "Oil and Natural Gas Corporation", "market": "BSE"},
    {"ticker": "ULTRACEMCO", "name": "UltraTech Cement Limited", "market": "BSE"},
    {"ticker": "ASIANPAINT", "name": "Asian Paints Limited", "market": "BSE"},
    {"ticker": "COALINDIA", "name": "Coal India Limited", "market": "BSE"},
    {"ticker": "BHEL", "name": "Bharat Heavy Electricals Ltd", "market": "BSE"},
    {"ticker": "SAIL", "name": "Steel Authority of India Ltd", "market": "BSE"},
    {"ticker": "VEDL", "name": "Vedanta Limited", "market": "BSE"},
    {"ticker": "IOC", "name": "Indian Oil Corporation Ltd", "market": "BSE"},
    {"ticker": "PNB", "name": "Punjab National Bank", "market": "BSE"},
    {"ticker": "BANKBARODA", "name": "Bank of Baroda", "market": "BSE"},
    {"ticker": "CANBK", "name": "Canara Bank", "market": "BSE"},
    {"ticker": "ZOMATO", "name": "Zomato Limited", "market": "BSE"},
    {"ticker": "PAYTM", "name": "One97 Communications (Paytm)", "market": "BSE"},
    {"ticker": "NYKAA", "name": "FSN E-Commerce (Nykaa)", "market": "BSE"},
    {"ticker": "SUZLON", "name": "Suzlon Energy Limited", "market": "BSE"},
    {"ticker": "YESBANK", "name": "Yes Bank Limited", "market": "BSE"},
    {"ticker": "IDFCFIRSTB", "name": "IDFC First Bank Limited", "market": "BSE"},

    # NASDAQ – US Stock Exchange
    {"ticker": "AAPL", "name": "Apple Inc.", "market": "NASDAQ"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ"},
    {"ticker": "GOOGL", "name": "Alphabet Inc. (Google)", "market": "NASDAQ"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "market": "NASDAQ"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ"},
    {"ticker": "META", "name": "Meta Platforms, Inc.", "market": "NASDAQ"},
    {"ticker": "TSLA", "name": "Tesla, Inc.", "market": "NASDAQ"},
    {"ticker": "AVGO", "name": "Broadcom Inc.", "market": "NASDAQ"},
    {"ticker": "ASML", "name": "ASML Holding N.V.", "market": "NASDAQ"},
    {"ticker": "COST", "name": "Costco Wholesale Corporation", "market": "NASDAQ"},
    {"ticker": "NFLX", "name": "Netflix, Inc.", "market": "NASDAQ"},
    {"ticker": "AMD", "name": "Advanced Micro Devices, Inc.", "market": "NASDAQ"},
    {"ticker": "ADBE", "name": "Adobe Inc.", "market": "NASDAQ"},
    {"ticker": "CSCO", "name": "Cisco Systems, Inc.", "market": "NASDAQ"},
    {"ticker": "QCOM", "name": "Qualcomm Incorporated", "market": "NASDAQ"},
    {"ticker": "INTC", "name": "Intel Corporation", "market": "NASDAQ"},
    {"ticker": "INTU", "name": "Intuit Inc.", "market": "NASDAQ"},
    {"ticker": "CMCSA", "name": "Comcast Corporation", "market": "NASDAQ"},
    {"ticker": "AMAT", "name": "Applied Materials, Inc.", "market": "NASDAQ"},
    {"ticker": "TXN", "name": "Texas Instruments Inc.", "market": "NASDAQ"},
    {"ticker": "AMGN", "name": "Amgen Inc.", "market": "NASDAQ"},
    {"ticker": "HON", "name": "Honeywell International Inc.", "market": "NASDAQ"},
    {"ticker": "SBUX", "name": "Starbucks Corporation", "market": "NASDAQ"},
    {"ticker": "MU", "name": "Micron Technology, Inc.", "market": "NASDAQ"},
    {"ticker": "PYPL", "name": "PayPal Holdings, Inc.", "market": "NASDAQ"},
    {"ticker": "GILD", "name": "Gilead Sciences, Inc.", "market": "NASDAQ"},
    {"ticker": "BKNG", "name": "Booking Holdings Inc.", "market": "NASDAQ"},
    {"ticker": "ADI", "name": "Analog Devices, Inc.", "market": "NASDAQ"},
    {"ticker": "LRCX", "name": "Lam Research Corporation", "market": "NASDAQ"},
    {"ticker": "PANW", "name": "Palo Alto Networks, Inc.", "market": "NASDAQ"},
    {"ticker": "REGN", "name": "Regeneron Pharmaceuticals", "market": "NASDAQ"},
    {"ticker": "VRTX", "name": "Vertex Pharmaceuticals", "market": "NASDAQ"},
    {"ticker": "KLAC", "name": "KLA Corporation", "market": "NASDAQ"},
    {"ticker": "SNPS", "name": "Synopsys, Inc.", "market": "NASDAQ"},
    {"ticker": "CDNS", "name": "Cadence Design Systems", "market": "NASDAQ"},
    {"ticker": "ABNB", "name": "Airbnb, Inc.", "market": "NASDAQ"},
    {"ticker": "MELI", "name": "MercadoLibre, Inc.", "market": "NASDAQ"},
    {"ticker": "WDAY", "name": "Workday, Inc.", "market": "NASDAQ"},
    {"ticker": "MRVL", "name": "Marvell Technology, Inc.", "market": "NASDAQ"},
    {"ticker": "ADSK", "name": "Autodesk, Inc.", "market": "NASDAQ"},
    {"ticker": "CRWD", "name": "CrowdStrike Holdings, Inc.", "market": "NASDAQ"},
    {"ticker": "MRNA", "name": "Moderna, Inc.", "market": "NASDAQ"},
    {"ticker": "LULU", "name": "Lululemon Athletica Inc.", "market": "NASDAQ"},
    {"ticker": "DXCM", "name": "DexCom, Inc.", "market": "NASDAQ"},
    {"ticker": "FTNT", "name": "Fortinet, Inc.", "market": "NASDAQ"},

    # NYSE – New York Stock Exchange
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "market": "NYSE"},
    {"ticker": "V", "name": "Visa Inc.", "market": "NYSE"},
    {"ticker": "DIS", "name": "The Walt Disney Company", "market": "NYSE"},
    {"ticker": "BRK.B", "name": "Berkshire Hathaway Inc.", "market": "NYSE"},
    {"ticker": "WMT", "name": "Walmart Inc.", "market": "NYSE"},
    {"ticker": "XOM", "name": "Exxon Mobil Corporation", "market": "NYSE"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "market": "NYSE"},
    {"ticker": "MA", "name": "Mastercard Incorporated", "market": "NYSE"},
    {"ticker": "PG", "name": "The Procter & Gamble Company", "market": "NYSE"},
    {"ticker": "HD", "name": "The Home Depot, Inc.", "market": "NYSE"},
    {"ticker": "CVX", "name": "Chevron Corporation", "market": "NYSE"},
    {"ticker": "ABBV", "name": "AbbVie Inc.", "market": "NYSE"},
    {"ticker": "LLY", "name": "Eli Lilly and Company", "market": "NYSE"},
    {"ticker": "BAC", "name": "Bank of America Corporation", "market": "NYSE"},
    {"ticker": "PFE", "name": "Pfizer Inc.", "market": "NYSE"},
    {"ticker": "KO", "name": "The Coca-Cola Company", "market": "NYSE"},
    {"ticker": "PEP", "name": "PepsiCo, Inc.", "market": "NYSE"},
    {"ticker": "TMO", "name": "Thermo Fisher Scientific Inc.", "market": "NYSE"},
    {"ticker": "MCD", "name": "McDonald's Corporation", "market": "NYSE"},
    {"ticker": "NKE", "name": "Nike, Inc.", "market": "NYSE"},
    {"ticker": "CRM", "name": "Salesforce, Inc.", "market": "NYSE"},
    {"ticker": "ABT", "name": "Abbott Laboratories", "market": "NYSE"},
    {"ticker": "DHR", "name": "Danaher Corporation", "market": "NYSE"},
    {"ticker": "WFC", "name": "Wells Fargo & Company", "market": "NYSE"},
    {"ticker": "MS", "name": "Morgan Stanley", "market": "NYSE"},
    {"ticker": "BMY", "name": "Bristol-Myers Squibb Company", "market": "NYSE"},
    {"ticker": "UNP", "name": "Union Pacific Corporation", "market": "NYSE"},
    {"ticker": "BA", "name": "The Boeing Company", "market": "NYSE"},
    {"ticker": "GS", "name": "The Goldman Sachs Group, Inc.", "market": "NYSE"},
    {"ticker": "CAT", "name": "Caterpillar Inc.", "market": "NYSE"},
    {"ticker": "GE", "name": "General Electric Company", "market": "NYSE"},
    {"ticker": "RTX", "name": "RTX Corporation", "market": "NYSE"},
    {"ticker": "IBM", "name": "International Business Machines (IBM)", "market": "NYSE"},
    {"ticker": "UNH", "name": "UnitedHealth Group Inc.", "market": "NYSE"},
    {"ticker": "VZ", "name": "Verizon Communications Inc.", "market": "NYSE"},
    {"ticker": "T", "name": "AT&T Inc.", "market": "NYSE"},
    {"ticker": "PM", "name": "Philip Morris International", "market": "NYSE"},
    {"ticker": "C", "name": "Citigroup Inc.", "market": "NYSE"},
    {"ticker": "TGT", "name": "Target Corporation", "market": "NYSE"},
    {"ticker": "AXP", "name": "American Express Company", "market": "NYSE"},
    {"ticker": "LMT", "name": "Lockheed Martin Corporation", "market": "NYSE"},
    {"ticker": "DE", "name": "Deere & Company", "market": "NYSE"},
    {"ticker": "MMM", "name": "3M Company", "market": "NYSE"},
    {"ticker": "F", "name": "Ford Motor Company", "market": "NYSE"},
    {"ticker": "GM", "name": "General Motors Company", "market": "NYSE"},
]

def search_companies_by_market(market: str, query: str = "") -> List[Dict[str, str]]:
    """
    Dynamically searches and returns companies strictly listed on the specified exchange market.
    Matches companies strictly based on the exact prefix of the company name:
    company_name.lower().startswith(query.lower())
    Never returns companies belonging to unselected exchange markets.
    Never uses substring matching or matches words inside the name that do not start with the prefix.
    """
    if not market:
        return []

    market_upper = market.strip().upper()
    q = query.strip().lower()

    # Strictly filter candidates belonging ONLY to the selected exchange
    market_stocks = [s for s in DEFAULT_TICKERS if s["market"].upper() == market_upper]

    if not q:
        return market_stocks

    # Strict prefix-based matching: only companies whose names begin with the exact prefix entered
    return [
        s for s in market_stocks
        if s["name"].lower().startswith(q)
    ]

def format_ticker_for_market(ticker: str, market: str) -> str:
    """
    Formats the ticker symbol for Yahoo Finance depending on market exchange.
    NSE tickers end in .NS (e.g. INFY.NS), BSE in .BO (e.g. TATAMOTORS.BO).
    """
    clean = ticker.strip().upper()
    suffix = MARKET_SUFFIX.get(market.upper(), "")

    # Strip existing suffixes if any
    clean_base = clean.replace(".NS", "").replace(".BO", "")

    if suffix and not clean.endswith(suffix):
        return f"{clean_base}{suffix}"
    return clean_base if not suffix else clean

def get_stock_quote(ticker: str, market: str = "NASDAQ") -> Dict[str, Any]:
    """
    Fetches real-time dynamic quote information from Yahoo Finance API.
    """
    yf_symbol = format_ticker_for_market(ticker, market)
    try:
        t = yf.Ticker(yf_symbol)
        fast = t.fast_info

        last_price = float(fast.last_price or 0.0)
        prev_close = float(fast.previous_close or last_price or 1.0)
        change = round(last_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        return {
            "ticker": ticker.upper(),
            "formatted_ticker": yf_symbol,
            "market": market,
            "last_price": round(last_price, 2),
            "previous_close": round(prev_close, 2),
            "change": change,
            "change_pct": change_pct,
            "currency": fast.currency or ("INR" if market in ["NSE", "BSE"] else "USD"),
            "day_high": round(float(fast.day_high or last_price), 2),
            "day_low": round(float(fast.day_low or last_price), 2),
            "year_high": round(float(fast.year_high or last_price), 2),
            "year_low": round(float(fast.year_low or last_price), 2),
            "market_cap": int(fast.market_cap or 0),
        }
    except Exception as e:
        # Graceful fallback for offline / rate limits
        return {
            "ticker": ticker.upper(),
            "formatted_ticker": yf_symbol,
            "market": market,
            "last_price": 0.0,
            "previous_close": 0.0,
            "change": 0.0,
            "change_pct": 0.0,
            "currency": "INR" if market in ["NSE", "BSE"] else "USD",
            "error": str(e),
        }

def get_historical_dataset(ticker: str, market: str, period_str: str) -> Dict[str, Any]:
    """
    Fetches dynamic historical OHLCV dataset and fundamental equity metrics
    from Yahoo Finance API for the requested analysis period.
    """
    yf_symbol = format_ticker_for_market(ticker, market)
    yf_period = PERIOD_MAP.get(period_str, "1y")

    try:
        t = yf.Ticker(yf_symbol)
        hist = t.history(period=yf_period)

        if hist.empty:
            return {
                "ticker": ticker,
                "period": period_str,
                "data_points": 0,
                "summary": f"No historical price data returned for {yf_symbol}.",
                "records": [],
            }

        start_price = float(hist["Close"].iloc[0])
        end_price = float(hist["Close"].iloc[-1])
        period_return = round(((end_price - start_price) / start_price) * 100, 2)
        highest_close = round(float(hist["High"].max()), 2)
        lowest_close = round(float(hist["Low"].min()), 2)
        avg_volume = int(hist["Volume"].mean())

        # Sample recent records (last 5 rows)
        recent_records = []
        for idx, row in hist.tail(5).iterrows():
            recent_records.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        # Fetch fundamental and valuation metrics
        info = {}
        try:
            info = t.info or {}
        except Exception:
            pass

        fast = None
        try:
            fast = t.fast_info
        except Exception:
            pass

        market_cap = 0
        fifty_day_avg = None
        two_hundred_day_avg = None
        year_high = None
        year_low = None

        if fast:
            market_cap = int(fast.market_cap or 0)
            fifty_day_avg = round(float(fast.fifty_day_average), 2) if fast.fifty_day_average else None
            two_hundred_day_avg = round(float(fast.two_hundred_day_average), 2) if fast.two_hundred_day_average else None
            year_high = round(float(fast.year_high), 2) if fast.year_high else None
            year_low = round(float(fast.year_low), 2) if fast.year_low else None

        currency = info.get("currency") or ("INR" if market in ["NSE", "BSE"] else "USD")

        return {
            "ticker": ticker.upper(),
            "formatted_symbol": yf_symbol,
            "market": market,
            "period": period_str,
            "currency": currency,
            "total_trading_days": len(hist),
            "start_date": hist.index[0].strftime("%Y-%m-%d"),
            "end_date": hist.index[-1].strftime("%Y-%m-%d"),
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "period_return_pct": period_return,
            "highest_price": highest_close,
            "lowest_price": lowest_close,
            "average_daily_volume": avg_volume,
            "recent_ohlcv": recent_records,
            # Fundamental & Technical Metrics
            "sector": info.get("sector") or "General Equities",
            "industry": info.get("industry") or "Diversified Operations",
            "market_cap": market_cap or info.get("marketCap", 0),
            "trailing_pe": round(float(info["trailingPE"]), 2) if info.get("trailingPE") else None,
            "forward_pe": round(float(info["forwardPE"]), 2) if info.get("forwardPE") else None,
            "trailing_eps": round(float(info["trailingEps"]), 2) if info.get("trailingEps") else None,
            "target_mean_price": round(float(info["targetMeanPrice"]), 2) if info.get("targetMeanPrice") else None,
            "recommendation_key": (info.get("recommendationKey") or "N/A").upper().replace("_", " "),
            "fifty_day_avg": fifty_day_avg,
            "two_hundred_day_avg": two_hundred_day_avg,
            "fifty_two_week_high": year_high,
            "fifty_two_week_low": year_low,
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "period": period_str,
            "error": str(e),
            "total_trading_days": 0,
        }
