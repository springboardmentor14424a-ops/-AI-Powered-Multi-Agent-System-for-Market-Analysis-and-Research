import asyncio
import json
from database.connection import AsyncSessionLocal
from routers.stocks import (
    search_stocks,
    get_historical_prices,
    get_stock_ohlcv,
    collect_and_store_ohlcv,
    get_saved_ohlcv,
)
from schemas.stock import CollectOHLCVRequest


async def run_tests():
    print("=" * 60)
    print("RUNNING VERIFICATION FOR MODULE 2 - FIRST 3 TASKS")
    print("=" * 60)

    # ─────────────────────────────────────────────────────────────
    # Task 1: Search for companies using their name or ticker symbol
    # ─────────────────────────────────────────────────────────────
    print("\n[TASK 1] Search for companies using their name or ticker symbol")
    
    # 1.1 Search by company name
    print("  -> Searching by Company Name: 'Apple'...")
    res_name = await search_stocks(q="Apple", market="NASDAQ")
    assert len(res_name) > 0, "No results returned for company name 'Apple'"
    print(f"     ✅ Found {len(res_name)} results. Top: {res_name[0].ticker} - {res_name[0].company_name} (${res_name[0].current_price})")

    # 1.2 Search by ticker symbol
    print("  -> Searching by Ticker Symbol: 'MSFT'...")
    res_ticker = await search_stocks(q="MSFT", market="NASDAQ")
    assert len(res_ticker) > 0, "No results returned for ticker 'MSFT'"
    print(f"     ✅ Found {len(res_ticker)} results. Top: {res_ticker[0].ticker} - {res_ticker[0].company_name}")

    # 1.3 Search across Indian market (NSE)
    print("  -> Searching Indian market by name: 'Reliance' (NSE)...")
    res_nse = await search_stocks(q="Reliance", market="NSE")
    assert len(res_nse) > 0, "No results returned for 'Reliance' on NSE"
    print(f"     ✅ Found {len(res_nse)} results. Top: {res_nse[0].ticker} - {res_nse[0].company_name} (Currency: {res_nse[0].currency})")

    # ─────────────────────────────────────────────────────────────
    # Task 2: Retrieve historical stock prices
    # ─────────────────────────────────────────────────────────────
    print("\n[TASK 2] Retrieve historical stock prices")
    print("  -> Retrieving historical stock prices for 'AAPL' (Period: 1mo, Interval: 1d)...")
    hist_prices = await get_historical_prices(ticker="AAPL", period="1mo", interval="1d")
    assert hist_prices.total_points > 0, "No historical price points returned"
    assert len(hist_prices.prices) == hist_prices.total_points
    print(f"     ✅ Retrieved {hist_prices.total_points} price points.")
    print(f"     Earliest: {hist_prices.prices[0].date} (Close: {hist_prices.prices[0].close})")
    print(f"     Latest:   {hist_prices.prices[-1].date} (Close: {hist_prices.prices[-1].close})")

    # ─────────────────────────────────────────────────────────────
    # Task 3: Collect OHLCV data: Open, High, Low, Close, and Volume
    # ─────────────────────────────────────────────────────────────
    print("\n[TASK 3] Collect OHLCV data: Open, High, Low, Close, and Volume")
    print("  -> Collecting live OHLCV candles for 'AAPL' (Period: 1mo, Interval: 1d)...")
    ohlcv = await get_stock_ohlcv(ticker="AAPL", period="1mo", interval="1d")
    assert ohlcv.total_bars > 0, "No OHLCV bars returned"
    sample_bar = ohlcv.data[0]
    assert hasattr(sample_bar, "open") and sample_bar.open is not None
    assert hasattr(sample_bar, "high") and sample_bar.high is not None
    assert hasattr(sample_bar, "low") and sample_bar.low is not None
    assert hasattr(sample_bar, "close") and sample_bar.close is not None
    assert hasattr(sample_bar, "volume") and sample_bar.volume is not None
    print(f"     ✅ Successfully collected {ohlcv.total_bars} OHLCV bars.")
    print(f"     Sample Bar: Date={sample_bar.date}, Open={sample_bar.open}, High={sample_bar.high}, Low={sample_bar.low}, Close={sample_bar.close}, Volume={sample_bar.volume:,}")
    print(f"     Summary Metrics:")
    print(f"       • Period Open:  {ohlcv.period_open}")
    print(f"       • Period High:  {ohlcv.period_high}")
    print(f"       • Period Low:   {ohlcv.period_low}")
    print(f"       • Period Close: {ohlcv.period_close}")
    print(f"       • Net Change:   {ohlcv.net_change} ({ohlcv.net_change_pct}%)")
    print(f"       • Total Volume: {ohlcv.total_volume:,}")

    # 3.2 Persist to PostgreSQL database
    print("\n  -> Persisting collected OHLCV data into PostgreSQL database...")
    async with AsyncSessionLocal() as session:
        req = CollectOHLCVRequest(ticker="AAPL", period="5d", interval="1d", company_name="Apple Inc.", market="NASDAQ")
        save_resp = await collect_and_store_ohlcv(req, db=session)
        assert save_resp.success is True
        print(f"     ✅ Database save response: {save_resp.message}")

        # Retrieve saved data from DB
        db_records = await get_saved_ohlcv(ticker="AAPL", interval="1d", db=session)
        assert len(db_records) >= 5
        print(f"     ✅ Successfully queried {len(db_records)} OHLCV records from PostgreSQL 'stock_ohlcv' table.")

    print("\n" + "=" * 60)
    print("ALL 3 TASKS COMPLETED & VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_tests())
