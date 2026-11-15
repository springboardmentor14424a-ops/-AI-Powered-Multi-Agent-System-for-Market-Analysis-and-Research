
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf

router = APIRouter(
    prefix="/api/stocks",
    tags=["Stock Search"]
)

@router.get("/search")
def search_stocks(
    query: str = Query(min_length=1, max_length=100)
):
    search_query = query.strip()

    if not search_query:
        raise HTTPException(
            status_code=400,
            detail="Please enter a company name or ticker"
        )

    try:
        search = yf.Search(
            search_query,
            max_results=10
        )

        results = []

        for item in search.quotes:
            if item.get("quoteType") != "EQUITY":
                continue

            results.append({
                "ticker": item.get("symbol"),
                "company_name": item.get("longname")
                    or item.get("shortname")
                    or item.get("symbol"),
                "exchange": item.get("exchange"),
                "type": item.get("quoteType")
            })

        return {
            "query": search_query,
            "results": results
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Stock search is temporarily unavailable. Please try again."
        )

