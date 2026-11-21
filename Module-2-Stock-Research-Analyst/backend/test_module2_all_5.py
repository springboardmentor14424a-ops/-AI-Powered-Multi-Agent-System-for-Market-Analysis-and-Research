import asyncio
from database.connection import AsyncSessionLocal
from routers.stocks import (
    search_stocks,
    get_historical_prices,
    get_stock_ohlcv,
    collect_and_store_ohlcv,
    get_company_profile,
    get_financial_statements,
    get_data_retrieval_audit_logs,
)
from schemas.stock import CollectOHLCVRequest


async def run_full_suite():
    print("=" * 65)
    print("VERIFICATION SUITE: MODULE 2 (TASKS 1 - 5)")
    print("=" * 65)

    async with AsyncSessionLocal() as session:
        # Task 1: Search by name and ticker
        print("\n[TASK 1] Search for companies using their name or ticker symbol")
        s1 = await search_stocks(q="Tesla", market="NASDAQ", db=session)
        assert len(s1) > 0, "Failed to search Tesla"
        print(f"  ✅ Search by name ('Tesla'): Found {len(s1)} results. Top: {s1[0].ticker} ({s1[0].company_name})")

        s2 = await search_stocks(q="TCS", market="NSE", db=session)
        assert len(s2) > 0, "Failed to search TCS"
        print(f"  ✅ Search by ticker ('TCS' / NSE): Found {len(s2)} results. Top: {s2[0].ticker} ({s2[0].currency})")

        # Task 2: Retrieve historical stock prices
        print("\n[TASK 2] Retrieve historical stock prices")
        hist = await get_historical_prices(ticker="MSFT", period="1mo", interval="1d", db=session)
        assert hist.total_points > 0
        print(f"  ✅ Retrieved {hist.total_points} price points for {hist.ticker} (Source: {hist.data_source})")

        # Task 3: Collect OHLCV data
        print("\n[TASK 3] Collect OHLCV data: Open, High, Low, Close, and Volume")
        ohlcv = await get_stock_ohlcv(ticker="MSFT", period="1mo", interval="1d", db=session)
        assert len(ohlcv.data) > 0
        b0 = ohlcv.data[0]
        print(f"  ✅ Collected {len(ohlcv.data)} OHLCV bars. Open={b0.open}, High={b0.high}, Low={b0.low}, Close={b0.close}, Volume={b0.volume:,}")
        print(f"     Summary: High={ohlcv.period_high}, Low={ohlcv.period_low}, Net Change={ohlcv.net_change} ({ohlcv.net_change_pct}%)")

        # Task 4: Retrieve available company profiles and financial statements
        print("\n[TASK 4] Retrieve available company profiles and financial statements")
        prof = await get_company_profile(ticker="MSFT", db=session)
        assert prof.company_name and prof.sector
        print(f"  ✅ Company Profile: {prof.company_name} ({prof.ticker})")
        print(f"     Sector: {prof.sector} | Industry: {prof.industry} | Employees: {prof.full_time_employees:,}")
        print(f"     Market Cap: ${prof.market_cap:,.0f} | P/E: {prof.pe_ratio} | Beta: {prof.beta}")
        print(f"     Executives: {[e.name for e in prof.key_executives[:3]]}")

        fin = await get_financial_statements(ticker="MSFT", db=session)
        assert len(fin.income_statements) > 0
        print(f"  ✅ Financial Statements:")
        print(f"     • Income Statements: {len(fin.income_statements)} periods. Latest Revenue: ${fin.income_statements[0].total_revenue:,.0f}" if fin.income_statements[0].total_revenue else f"     • Income Statements: {len(fin.income_statements)} periods.")
        cash_val = fin.balance_sheets[0].cash_and_equivalents if fin.balance_sheets and fin.balance_sheets[0].cash_and_equivalents is not None else 0
        print(f"     • Balance Sheets:    {len(fin.balance_sheets)} periods. Cash & Equiv:   ${cash_val:,.0f}")
        op_cf = fin.cash_flows[0].operating_cash_flow if fin.cash_flows and fin.cash_flows[0].operating_cash_flow is not None else 0
        print(f"     • Cash Flows:        {len(fin.cash_flows)} periods. Operating CF:  ${op_cf:,.0f}")

        # Task 5: Record data sources and retrieval timestamps
        print("\n[TASK 5] Record data sources and retrieval timestamps")
        print(f"  ✅ Profile Provenance:    Source='{prof.data_source}', Timestamp={prof.retrieval_timestamp.isoformat()}")
        print(f"  ✅ Financials Provenance: Source='{fin.data_source}', Timestamp={fin.retrieval_timestamp.isoformat()}")
        print(f"  ✅ OHLCV Provenance:      Source='{ohlcv.data_source}', Timestamp={ohlcv.retrieval_timestamp.isoformat()}")

        # Check DB audit logs
        logs = await get_data_retrieval_audit_logs(ticker="MSFT", limit=10, db=session)
        assert len(logs) >= 3, "Audit logs missing entries for MSFT"
        print(f"  ✅ Verified {len(logs)} audit log records saved in PostgreSQL 'data_retrieval_audit_logs' table for MSFT:")
        for log in logs[:4]:
            print(f"     • [{log.retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}] Type: {log.data_type:<20} Source: {log.data_source} (Status: {log.status})")

    print("\n" + "=" * 65)
    print("ALL 5 TASKS VERIFIED AND WORKING PERFECTLY!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_full_suite())
