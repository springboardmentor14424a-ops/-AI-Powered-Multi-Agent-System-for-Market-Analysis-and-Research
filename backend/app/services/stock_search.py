
import yfinance as yf


def search_stocks(query: str):
    """
    Search for Indian companies by company name or ticker.
    Supports NSE and BSE listings.
    """

    try:
        search = yf.Search(query, max_results=10)

        results = []

        for stock in search.quotes:
            symbol = stock.get("symbol", "")

            # Only include NSE and BSE stocks
            if symbol.endswith(".NS"):
                market = "NSE"
            elif symbol.endswith(".BO"):
                market = "BSE"
            else:
                continue

            results.append({
                "company_name": (
                    stock.get("longname")
                    or stock.get("shortname")
                    or symbol
                ),
                "ticker": symbol,
                "market": market,
                "exchange": stock.get("exchDisp", ""),
                "sector": stock.get("sector", "")
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
