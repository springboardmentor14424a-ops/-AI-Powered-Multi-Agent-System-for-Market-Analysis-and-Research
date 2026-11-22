import yfinance as yf


def search_stocks(query: str):
    """
    Search for companies by company name or ticker.
    Supports NSE, BSE, NASDAQ, and NYSE listings using yfinance.
    """
    try:
        search = yf.Search(query, max_results=15)

        results = []
        seen = set()

        for stock in search.quotes:
            symbol = (stock.get("symbol") or "").strip().upper()
            if not symbol:
                continue

            # Filter search results to equities where typeDisp is available
            type_disp = (stock.get("typeDisp") or "").strip().lower()
            if type_disp and type_disp not in ("equity", "common stock"):
                continue

            exch_disp = (stock.get("exchDisp") or "").strip().upper()
            exch_code = (stock.get("exchange") or "").strip().upper()

            # Market identification rules:
            # 1. NSE: symbol ends with .NS, exchDisp is NSE, or exchange code is NSI
            if symbol.endswith(".NS") or exch_disp == "NSE" or exch_code == "NSI":
                market = "NSE"
                ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"

            # 2. BSE: symbol ends with .BO, exchDisp is BSE or Bombay, or exchange code is BSE
            elif symbol.endswith(".BO") or exch_disp in ("BSE", "BOMBAY") or exch_code == "BSE":
                market = "BSE"
                ticker = symbol if symbol.endswith(".BO") else f"{symbol}.BO"

            # 3. NASDAQ: exchDisp is NASDAQ, or exchange code is one of NMS, NGS, NCM, NAS
            elif exch_disp == "NASDAQ" or exch_code in ("NMS", "NGS", "NCM", "NAS"):
                market = "NASDAQ"
                ticker = symbol.split(".")[0]

            # 4. NYSE: exchDisp is NYSE, or exchange code is one of NYQ, NYS, ASE
            elif exch_disp == "NYSE" or exch_code in ("NYQ", "NYS", "ASE"):
                market = "NYSE"
                ticker = symbol.split(".")[0]

            else:
                continue

            # Deduplicate by (ticker, market)
            key = (ticker, market)
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "company_name": (
                    stock.get("longname")
                    or stock.get("shortname")
                    or ticker
                ),
                "ticker": ticker,
                "market": market,
                "exchange": stock.get("exchDisp") or exch_disp or market,
                "sector": stock.get("sector") or stock.get("industry") or ""
            })

        return {
            "success": True,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Stock search failed: {str(e)}",
            "results": []
        }
