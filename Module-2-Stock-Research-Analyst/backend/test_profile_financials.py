import asyncio
from database.connection import AsyncSessionLocal
from routers.stocks import get_company_profile, get_financial_statements, get_data_retrieval_audit_logs

async def test_new_endpoints():
    async with AsyncSessionLocal() as session:
        print("=== Testing Company Profile (AAPL) ===")
        p = await get_company_profile(ticker="AAPL", db=session)
        print("Ticker:", p.ticker, "| Name:", p.company_name)
        print("Sector:", p.sector, "| Industry:", p.industry)
        print("Data Source:", p.data_source)
        print("Retrieval Timestamp:", p.retrieval_timestamp.isoformat())
        print("Market Cap:", p.market_cap, "| P/E:", p.pe_ratio)
        print("Key Executives:", [e.name for e in p.key_executives])

        print("\n=== Testing Financial Statements (AAPL) ===")
        f = await get_financial_statements(ticker="AAPL", db=session)
        print("Income statements count:", len(f.income_statements))
        if f.income_statements:
            print("Latest Income Statement:", f.income_statements[0].model_dump())
        print("Balance sheets count:", len(f.balance_sheets))
        print("Cash flows count:", len(f.cash_flows))
        print("Data Source:", f.data_source)
        print("Retrieval Timestamp:", f.retrieval_timestamp.isoformat())

        print("\n=== Testing Company Profile (RELIANCE.NS) ===")
        p_rel = await get_company_profile(ticker="RELIANCE.NS", db=session)
        print("Reliance Sector:", p_rel.sector, "| Currency:", p_rel.currency, "| Source:", p_rel.data_source)

        print("\n=== Testing Financial Statements (RELIANCE.NS) ===")
        f_rel = await get_financial_statements(ticker="RELIANCE.NS", db=session)
        print("Reliance Income stmts count:", len(f_rel.income_statements))
        if f_rel.income_statements:
            print("Reliance Sample Revenue:", f_rel.income_statements[0].total_revenue)

        print("\n=== Testing Data Retrieval Audit Logs ===")
        logs = await get_data_retrieval_audit_logs(db=session, limit=10)
        print(f"Retrieved {len(logs)} audit log entries:")
        for l in logs[:5]:
            print(f"  • [{l.retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {l.ticker} - {l.data_type} from '{l.data_source}' ({l.status})")

    print("\nALL NEW PROFILE & FINANCIALS & AUDIT LOG TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_new_endpoints())
