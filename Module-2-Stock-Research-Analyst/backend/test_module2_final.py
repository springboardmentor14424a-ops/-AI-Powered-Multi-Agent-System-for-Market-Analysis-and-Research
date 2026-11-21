import asyncio
import sys
from datetime import datetime
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from models.user import StockOHLCV, CompanyFinancialsProfile, DataRetrievalAuditLog, User
from routers.stocks import (
    search_stocks,
    get_historical_prices,
    get_stock_ohlcv,
    collect_and_store_ohlcv,
    get_company_profile,
    get_financial_statements,
    get_data_retrieval_audit_logs,
    get_supported_markets,
    get_market_detail,
    get_market_stocks,
)
from routers.google_auth import google_login
from schemas.stock import CollectOHLCVRequest
from schemas.auth import GoogleLoginRequest
from starlette.responses import Response

async def run_comprehensive_tests():
    print("=" * 75)
    print("🚀 MODULE 2 & GOOGLE AUTH COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 75)

    async with AsyncSessionLocal() as db:
        # ─────────────────────────────────────────────────────────────────────
        # TEST 1: SUPPORT SELECTED STOCK MARKETS (NSE/BSE & NASDAQ/NYSE)
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 1] Supporting Selected Stock Markets (NSE, BSE, NASDAQ, NYSE)")
        markets = await get_supported_markets()
        market_codes = [m.code for m in markets]
        print(f"  ✓ Supported Markets Count: {len(markets)}")
        print(f"  ✓ Market Codes: {market_codes}")
        assert "NSE" in market_codes, "NSE must be supported"
        assert "BSE" in market_codes, "BSE must be supported"
        assert "NASDAQ" in market_codes, "NASDAQ must be supported"
        assert "NYSE" in market_codes, "NYSE must be supported"

        for m in markets:
            print(f"    • {m.code}: {m.name} ({m.country}) | Currency: {m.currency_symbol} {m.currency} | Benchmark: {m.index_name} | Popular stocks: {len(m.popular_stocks)}")
            assert m.currency in ("INR", "USD")
            assert len(m.popular_stocks) > 0

        nse_detail = await get_market_detail("NSE")
        assert nse_detail.code == "NSE" and nse_detail.currency == "INR"
        print(f"  ✓ Market Detail (NSE): {nse_detail.name}, Hours: {nse_detail.trading_hours}")

        nasdaq_stocks = await get_market_stocks("NASDAQ")
        print(f"  ✓ NASDAQ Top Benchmark Equities: {[s.ticker for s in nasdaq_stocks]}")
        assert len(nasdaq_stocks) >= 5

        # ─────────────────────────────────────────────────────────────────────
        # TEST 2: SEARCH COMPANIES BY NAME OR TICKER
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 2] Search Companies by Name or Ticker Symbol")
        res_aapl = await search_stocks(q="AAPL", market="NASDAQ", db=db)
        print(f"  ✓ Search 'AAPL' (NASDAQ): Found {len(res_aapl)} results -> Ticker: {res_aapl[0].ticker}, Name: {res_aapl[0].company_name}, Price: ${res_aapl[0].current_price}")
        assert any(r.ticker == "AAPL" for r in res_aapl)

        res_rel = await search_stocks(q="Reliance", market="NSE", db=db)
        print(f"  ✓ Search 'Reliance' (NSE): Found {len(res_rel)} results -> Ticker: {res_rel[0].ticker}, Name: {res_rel[0].company_name}, Currency: {res_rel[0].currency}")
        assert len(res_rel) > 0

        # ─────────────────────────────────────────────────────────────────────
        # TEST 3: HISTORICAL PRICES AS TIME SERIES
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 3] Retrieve Historical Stock Prices (Stock vs Time)")
        hist_aapl = await get_historical_prices(ticker="AAPL", period="1mo", interval="1d", market="NASDAQ", db=db)
        print(f"  ✓ AAPL Historical Points: {hist_aapl.total_points} data points from {hist_aapl.prices[0].date} to {hist_aapl.prices[-1].date}")
        print(f"    Source: {hist_aapl.data_source} | Timestamp: {hist_aapl.retrieval_timestamp.isoformat()}")
        assert hist_aapl.total_points > 0

        hist_nse = await get_historical_prices(ticker="RELIANCE.NS", period="1mo", interval="1d", market="NSE", db=db)
        print(f"  ✓ RELIANCE.NS Historical Points: {hist_nse.total_points} points | Currency: {hist_nse.currency}")
        assert hist_nse.total_points > 0

        # ─────────────────────────────────────────────────────────────────────
        # TEST 4: OHLCV DATA COLLECTION & QUANTITATIVE DATA VALIDATION
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 4] Collect OHLCV Data & Validate Missing Values, Duplicate Dates, Inconsistent Bounds")
        ohlcv = await get_stock_ohlcv(ticker="AAPL", period="1mo", interval="1d", market="NASDAQ", db=db)
        print(f"  ✓ AAPL OHLCV Candles: {ohlcv.total_bars} bars | Period Open: ${ohlcv.period_open} | High: ${ohlcv.period_high} | Low: ${ohlcv.period_low} | Close: ${ohlcv.period_close}")
        val_summary = ohlcv.validation_summary
        print(f"  ✓ Quantitative Data Validation Report:")
        print(f"    • Status: {val_summary['status']} ({val_summary['data_integrity_score']} score)")
        print(f"    • Checked: {val_summary['total_records_checked']} records | Clean: {val_summary['clean_bars_count']}")
        print(f"    • Missing Values Imputed: {val_summary['missing_values_imputed']}")
        print(f"    • Duplicate Dates Deduplicated: {val_summary['duplicates_removed']}")
        print(f"    • Inconsistencies Corrected: {val_summary['inconsistencies_corrected']}")
        assert val_summary["status"] == "VALIDATED_CLEAN"
        assert val_summary["clean_bars_count"] > 0

        # Persist to database
        collect_req = CollectOHLCVRequest(ticker="AAPL", period="1mo", interval="1d", market="NASDAQ", company_name="Apple Inc.")
        save_resp = await collect_and_store_ohlcv(req=collect_req, db=db)
        print(f"  ✓ Database Persistence: {save_resp.message} (Stored {save_resp.bars_collected} candles)")
        assert save_resp.success is True

        # ─────────────────────────────────────────────────────────────────────
        # TEST 5: COMPANY PROFILE & FINANCIAL STATEMENTS
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 5] Retrieve Company Profiles & Multi-Period Financial Statements")
        profile = await get_company_profile(ticker="AAPL", market="NASDAQ", db=db)
        print(f"  ✓ Company Profile: {profile.company_name} ({profile.ticker}) | Sector: {profile.sector} | Country: {profile.country}")
        print(f"    Market Cap: ${profile.market_cap:,.0f} | P/E: {profile.pe_ratio} | Source: {profile.data_source}")
        assert profile.company_name and profile.market_cap

        financials = await get_financial_statements(ticker="AAPL", market="NASDAQ", db=db)
        print(f"  ✓ Financial Statements: {len(financials.income_statements)} Income Stmts, {len(financials.balance_sheets)} Balance Sheets, {len(financials.cash_flows)} Cash Flows")
        print(f"    Latest Period Revenue: ${financials.income_statements[0].total_revenue:,.0f} | Source: {financials.data_source}")
        assert len(financials.income_statements) > 0

        # Test Indian Stock Profile & Financials
        infy_profile = await get_company_profile(ticker="INFY.NS", market="NSE", db=db)
        print(f"  ✓ Indian Stock Profile (INFY.NS): {infy_profile.company_name} | Currency: {infy_profile.currency} | Market: {infy_profile.market}")
        assert infy_profile.currency == "INR"

        # ─────────────────────────────────────────────────────────────────────
        # TEST 6: DATA RETRIEVAL AUDIT LOGS (PROVENANCE TRACKING)
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 6] Record Data Sources & Retrieval Timestamps (Provenance Audit Logs)")
        logs = await get_data_retrieval_audit_logs(ticker=None, limit=10, db=db)
        print(f"  ✓ Retrieved {len(logs)} Audit Provenance Logs from DB:")
        for log in logs[:4]:
            print(f"    [{log.retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}] Ticker: {log.ticker} | Type: {log.data_type} | Source: {log.data_source} | Status: {log.status}")
        assert len(logs) > 0

        # ─────────────────────────────────────────────────────────────────────
        # TEST 7: GOOGLE OAUTH & INSTANT DEMO LOGIN VERIFICATION
        # ─────────────────────────────────────────────────────────────────────
        print("\n[TEST 7] Google OAuth & Instant Demo Sign-In Authentication")
        fake_response = Response()
        g_login = await google_login(
            payload=GoogleLoginRequest(credential="demo_google_analyst_session"),
            response=fake_response,
            db=db,
        )
        print(f"  ✓ Google Sign-In Success: Access Token Issued -> Bearer {g_login.access_token[:20]}...")
        print(f"  ✓ Authenticated User: {g_login.user.full_name} ({g_login.user.email}) | ID: {g_login.user.id}")
        assert g_login.access_token and g_login.user.email

    print("\n" + "=" * 75)
    print("🎉 ALL TESTS PASSED! MODULE 2 & AUTH FULLY OPERATIONAL AND PRESENTATION READY!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
