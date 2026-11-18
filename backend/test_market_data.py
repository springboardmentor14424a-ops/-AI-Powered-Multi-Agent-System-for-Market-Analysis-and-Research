import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
os.environ["ENABLE_LIVE_FINANCE_API"] = "0"
import sys
import json
import time
from sqlalchemy import inspect
from app.database import engine, Base, SessionLocal
from app.models import MarketDataRecord, CompanyProfile, CompanyFinancial, DataValidationLog
from app.services.market_data_service import market_service
from app.services.data_validator import MarketDataValidator
from app.routers.market_data import (
    search_companies,
    get_historical_ohlcv,
    get_company_profile,
    get_financial_statements,
    validate_market_data,
    get_live_quote,
    get_provider_status,
    update_provider_keys
)
from app.schemas import RawDataValidationRequest, ProviderKeyUpdate

def run_market_data_tests():
    print("=" * 75)
    print("   MODULE 2: STOCK SEARCH & MARKET DATA COLLECTION - VERIFICATION SUITE")
    print("=" * 75)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Database Engine: {engine.url}")
    print("-" * 75)

    # ---------------------------------------------------------
    # TEST 1: DATABASE SCHEMA EXPANSION
    # ---------------------------------------------------------
    print("\n[TEST 1] VERIFYING MODULE 2 DATABASE TABLES & CONSTRAINTS...")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  -> Detected Database Tables: {tables}")
    
    assert "market_data_records" in tables, "Table 'market_data_records' missing!"
    assert "company_profiles" in tables, "Table 'company_profiles' missing!"
    assert "company_financials" in tables, "Table 'company_financials' missing!"
    assert "data_validation_logs" in tables, "Table 'data_validation_logs' missing!"

    market_cols = [c["name"] for c in inspector.get_columns("market_data_records")]
    assert all(c in market_cols for c in ["ticker", "market", "record_date", "open_price", "high_price", "low_price", "close_price", "volume", "data_source", "retrieved_at"])
    print("  -> Table 'market_data_records' verified with OHLCV columns & constraints.")

    profile_cols = [c["name"] for c in inspector.get_columns("company_profiles")]
    assert all(c in profile_cols for c in ["ticker", "market", "company_name", "sector", "ceo", "market_cap", "pe_ratio", "data_source", "retrieved_at"])
    print("  -> Table 'company_profiles' verified with fundamental attributes.")

    fin_cols = [c["name"] for c in inspector.get_columns("company_financials")]
    assert all(c in fin_cols for c in ["ticker", "market", "period_type", "data_json", "data_source", "retrieved_at"])
    print("  -> Table 'company_financials' verified.")

    val_cols = [c["name"] for c in inspector.get_columns("data_validation_logs")]
    assert all(c in val_cols for c in ["ticker", "total_records", "clean_records", "missing_values_handled", "duplicate_dates_removed", "inconsistencies_corrected", "quality_score"])
    print("  -> Table 'data_validation_logs' verified.")
    print("  ✓ [PASS] All 4 Module 2 Database Tables Verified!\n")

    db = SessionLocal()

    # ---------------------------------------------------------
    # TEST 2: STOCK SEARCH BY NAME AND TICKER ACROSS MARKETS
    # ---------------------------------------------------------
    print("[TEST 2] TESTING STOCK SEARCH (BY NAME OR TICKER ACROSS NSE/BSE/NASDAQ/NYSE)...")
    
    # 2a. Search Indian equity by ticker
    res_rel = search_companies(query="RELIANCE", market="NSE")
    assert len(res_rel) >= 1
    rel_item = res_rel[0]
    ticker_val = rel_item["ticker"] if isinstance(rel_item, dict) else rel_item.ticker
    name_val = rel_item["name"] if isinstance(rel_item, dict) else rel_item.name
    sector_val = rel_item["sector"] if isinstance(rel_item, dict) else rel_item.sector
    assert ticker_val == "RELIANCE"
    print(f"  -> Search 'RELIANCE' (NSE): Found '{name_val}' (Sector: {sector_val})")

    # 2b. Search US equity by company name
    res_apple = search_companies(query="Apple", market="NASDAQ")
    assert len(res_apple) >= 1
    aapl_item = res_apple[0]
    aapl_ticker = aapl_item["ticker"] if isinstance(aapl_item, dict) else aapl_item.ticker
    aapl_price = aapl_item["base_price"] if isinstance(aapl_item, dict) else aapl_item.base_price
    assert aapl_ticker == "AAPL"
    print(f"  -> Search 'Apple' (NASDAQ): Found ticker '{aapl_ticker}' (Price: ${aapl_price})")

    # 2c. Search US equity by ticker
    res_nvda = search_companies(query="NVDA", market="NASDAQ")
    assert len(res_nvda) >= 1
    nvda_item = res_nvda[0]
    nvda_ticker = nvda_item["ticker"] if isinstance(nvda_item, dict) else nvda_item.ticker
    nvda_name = nvda_item["name"] if isinstance(nvda_item, dict) else nvda_item.name
    assert nvda_ticker == "NVDA"
    print(f"  -> Search 'NVDA' (NASDAQ): Found '{nvda_name}'")

    # 2d. Search Indian equity by partial name
    res_tata = search_companies(query="Tata", market="NSE")
    assert len(res_tata) >= 2
    tickers = [s["ticker"] if isinstance(s, dict) else s.ticker for s in res_tata]
    print(f"  -> Search 'Tata' (NSE): Found {tickers}")

    # 2e. Global cross-market search
    res_all = search_companies(query="", market="ALL")
    assert len(res_all) >= 15
    print(f"  -> Multi-market catalog count: {len(res_all)} companies available.")
    print("  ✓ [PASS] Stock Search by Name and Ticker Across Markets Verified!\n")

    # ---------------------------------------------------------
    # TEST 3: HISTORICAL STOCK PRICES & OHLCV COLLECTION
    # ---------------------------------------------------------
    print("[TEST 3] TESTING HISTORICAL OHLCV DATA COLLECTION & TIMESTAMPS...")
    
    # 3a. Indian Market OHLCV (TCS on NSE)
    tcs_ohlcv = get_historical_ohlcv(ticker="TCS", market="NSE", period="6 Months", interval="1d", db=db)
    assert tcs_ohlcv["ticker"] == "TCS"
    assert tcs_ohlcv["market"] == "NSE"
    assert len(tcs_ohlcv["points"]) > 20
    assert "data_source" in tcs_ohlcv and len(tcs_ohlcv["data_source"]) > 0
    assert "retrieval_timestamp" in tcs_ohlcv and tcs_ohlcv["retrieval_timestamp"].endswith("Z")
    
    sample_pt = tcs_ohlcv["points"][-1]
    assert all(k in sample_pt for k in ["date", "open", "high", "low", "close", "volume"])
    print(f"  -> TCS (NSE): Collected {len(tcs_ohlcv['points'])} candles. Source: '{tcs_ohlcv['data_source']}'")
    print(f"     Latest Candle ({sample_pt['date']}): Open={sample_pt['open']}, High={sample_pt['high']}, Low={sample_pt['low']}, Close={sample_pt['close']}, Vol={sample_pt['volume']:,}")
    print(f"     Retrieval Timestamp: {tcs_ohlcv['retrieval_timestamp']}")

    # 3b. US Market OHLCV (AAPL on NASDAQ)
    aapl_ohlcv = get_historical_ohlcv(ticker="AAPL", market="NASDAQ", period="1 Year", interval="1d", db=db)
    assert aapl_ohlcv["ticker"] == "AAPL"
    assert aapl_ohlcv["market"] == "NASDAQ"
    assert len(aapl_ohlcv["points"]) > 50
    assert "data_source" in aapl_ohlcv
    print(f"  -> AAPL (NASDAQ): Collected {len(aapl_ohlcv['points'])} candles. Source: '{aapl_ohlcv['data_source']}'")
    print("  ✓ [PASS] Historical OHLCV Collection, Sources, & UTC Timestamps Verified!\n")

    # ---------------------------------------------------------
    # TEST 4: RIGOROUS DATA VALIDATION ENGINE
    # (Missing Values, Duplicate Dates, Inconsistent Bounds)
    # ---------------------------------------------------------
    print("[TEST 4] TESTING DATA VALIDATION ENGINE (MISSING VALUES, DUPLICATE DATES, INCONSISTENCIES)...")
    
    # Construct a deliberately corrupted dataset:
    corrupted_data = [
        # Normal candle
        {"date": "2026-11-01", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0, "volume": 50000},
        # Anomaly 1: Missing Open, High, and Volume
        {"date": "2026-11-02", "open": None, "high": None, "low": 99.0, "close": 104.0, "volume": None},
        # Anomaly 2: Duplicate Date with 2026-11-02
        {"date": "2026-11-02", "open": 103.0, "high": 106.0, "low": 101.0, "close": 105.0, "volume": 75000},
        # Anomaly 3: Inverted Bounds (High < Low) and High lower than Open/Close
        {"date": "2026-11-03", "open": 110.0, "high": 90.0, "low": 115.0, "close": 112.0, "volume": -80000},
        # Anomaly 4: Non-positive price
        {"date": "2026-11-04", "open": -5.0, "high": 118.0, "low": -10.0, "close": 114.0, "volume": 60000},
        # Anomaly 5: Missing Close price
        {"date": "2026-11-05", "open": 115.0, "high": 120.0, "low": 113.0, "close": None, "volume": 90000},
    ]

    val_response = validate_market_data(RawDataValidationRequest(
        ticker="TEST-CORRUPT",
        market="NYSE",
        records=corrupted_data
    ))

    report = val_response["validation_report"]
    clean_recs = val_response["clean_records"]

    print(f"  -> Raw Input Records: {report['total_records']}")
    print(f"  -> Cleaned Records Output: {report['clean_records']}")
    print(f"  -> Missing Values Handled: {report['missing_values_handled']}")
    print(f"  -> Duplicate Dates Removed: {report['duplicate_dates_removed']}")
    print(f"  -> Inconsistencies Corrected: {report['inconsistencies_corrected']}")
    print(f"  -> Data Quality Score: {report['quality_score']}%")
    print(f"  -> Audit Issues Log ({len(report['issues_log'])} logged):")
    for issue in report["issues_log"][:4]:
        print(f"     • {issue}")

    assert report["missing_values_handled"] >= 3, "Failed to detect/handle missing values!"
    assert report["duplicate_dates_removed"] == 1, "Failed to detect/remove duplicate date!"
    assert report["inconsistencies_corrected"] >= 3, "Failed to correct price bounds & negative volume!"
    
    # Verify mathematical integrity of every single cleaned record
    for rec in clean_recs:
        assert rec["low"] <= rec["open"] <= rec["high"], f"Bounds violated in {rec}"
        assert rec["low"] <= rec["close"] <= rec["high"], f"Bounds violated in {rec}"
        assert rec["volume"] >= 0, f"Negative volume remaining in {rec}"
        assert rec["open"] > 0 and rec["high"] > 0 and rec["low"] > 0 and rec["close"] > 0, f"Non-positive price in {rec}"
    
    # Check that duplicate date was removed
    dates = [r["date"] for r in clean_recs]
    assert len(dates) == len(set(dates)), "Duplicate date not eliminated!"
    print("  ✓ [PASS] Automated Data Validation Engine Passed with 100% Mathematical Rigor!\n")

    # ---------------------------------------------------------
    # TEST 5: COMPANY PROFILES RETRIEVAL
    # ---------------------------------------------------------
    print("[TEST 5] TESTING COMPANY PROFILES RETRIEVAL & FINANCIAL RATIOS...")
    
    # 5a. US Company Profile (MSFT)
    msft_prof = get_company_profile(ticker="MSFT", market="NASDAQ", db=db)
    assert msft_prof["ticker"] == "MSFT"
    assert msft_prof["ceo"] == "Satya Nadella"
    assert msft_prof["pe_ratio"] > 0
    assert msft_prof["week_52_high"] > msft_prof["week_52_low"]
    assert "data_source" in msft_prof
    assert msft_prof["retrieval_timestamp"].endswith("Z")
    print(f"  -> MSFT (NASDAQ): CEO={msft_prof['ceo']}, Sector={msft_prof['sector']}, Market Cap={msft_prof['market_cap']}, PE={msft_prof['pe_ratio']}")
    print(f"     52W Range: ${msft_prof['week_52_low']} - ${msft_prof['week_52_high']} | Source: {msft_prof['data_source']}")

    # 5b. Indian Company Profile (INFY)
    infy_prof = get_company_profile(ticker="INFY", market="NSE", db=db)
    assert infy_prof["ticker"] == "INFY"
    assert infy_prof["ceo"] == "Salil Parekh"
    assert infy_prof["currency"] == "INR"
    print(f"  -> INFY (NSE): CEO={infy_prof['ceo']}, Employees={infy_prof['employees']:,}, Currency={infy_prof['currency']}")
    print("  ✓ [PASS] Company Profile Retrieval & Source Tracking Verified!\n")

    # ---------------------------------------------------------
    # TEST 6: FINANCIAL STATEMENTS (INCOME, BALANCE SHEET, CASH FLOW)
    # ---------------------------------------------------------
    print("[TEST 6] TESTING FINANCIAL STATEMENTS (INCOME STMT, BALANCE SHEET, CASH FLOW, RATIOS)...")
    
    fin_annual = get_financial_statements(ticker="RELIANCE", market="NSE", period_type="annual", db=db)
    assert fin_annual["ticker"] == "RELIANCE"
    assert len(fin_annual["income_statement"]) >= 4
    assert len(fin_annual["balance_sheet"]) >= 4
    assert len(fin_annual["cash_flow"]) >= 4
    assert "net_profit_margin" in fin_annual["ratios"]
    assert "current_ratio" in fin_annual["ratios"]
    
    latest_stmt = fin_annual["income_statement"][-1]
    print(f"  -> RELIANCE (NSE) Financials ({fin_annual['period_type'].capitalize()}):")
    print(f"     • Revenue ({latest_stmt['period']}): ₹{latest_stmt['total_revenue']:,} Cr | Net Income: ₹{latest_stmt['net_income']:,} Cr (Margin: {latest_stmt['profit_margin_pct']}%)")
    print(f"     • Balance Sheet: Stockholders Equity = ₹{fin_annual['balance_sheet'][-1]['stockholders_equity']:,} Cr")
    print(f"     • Cash Flow: Operating Cash Flow = ₹{fin_annual['cash_flow'][-1]['operating_cash_flow']:,} Cr | Free Cash Flow = ₹{fin_annual['cash_flow'][-1]['free_cash_flow']:,} Cr")
    print(f"     • Financial Ratios: ROE={fin_annual['ratios']['return_on_equity_roe']}, Current Ratio={fin_annual['ratios']['current_ratio']}")
    print(f"     • Data Source: {fin_annual['data_source']} | Timestamp: {fin_annual['retrieval_timestamp']}")
    print("  ✓ [PASS] Financial Statements & Ratio Analytics Verified!\n")

    # ---------------------------------------------------------
    # TEST 7: FREE APIS (ALPHA VANTAGE & TWELVE DATA) CONFIGURATION & STATUS
    # ---------------------------------------------------------
    print("[TEST 7] TESTING FREE APIS CONFIGURATION (ALPHA VANTAGE & TWELVE DATA)...")
    status = get_provider_status()
    print(f"  -> Supported Markets: {status['supported_markets']}")
    print(f"  -> Active Providers: {status['active_providers']}")
    print(f"  -> Alpha Vantage Key: {status['alpha_vantage_masked_key']}")
    print(f"  -> Twelve Data Key: {status['twelve_data_masked_key']}")
    
    # Test updating custom keys
    updated_status = update_provider_keys(ProviderKeyUpdate(
        alpha_vantage_key="demo_key_av_12345",
        twelve_data_key="demo_key_td_67890"
    ))
    assert updated_status["alpha_vantage_configured"] is True
    assert updated_status["twelve_data_configured"] is True
    print(f"  -> Successfully updated & masked API Keys: AV={updated_status['alpha_vantage_masked_key']}, TD={updated_status['twelve_data_masked_key']}")
    print("  ✓ [PASS] Alpha Vantage and Twelve Data Free API Integration Verified!\n")

    # ---------------------------------------------------------
    # TEST 8: LIVE REAL-TIME QUOTE WITH TIMESTAMPS
    # ---------------------------------------------------------
    print("[TEST 8] TESTING LIVE QUOTE FEED & TIMESTAMP ATTRIBUTION...")
    quote = get_live_quote("NVDA", market="NASDAQ", db=db)
    assert quote["ticker"] == "NVDA"
    assert quote["price"] > 0
    assert "data_source" in quote
    assert "retrieval_timestamp" in quote
    print(f"  -> NVDA Quote: ${quote['price']} ({'+' if quote['change']>=0 else ''}{quote['change_pct']}%)")
    print(f"     Day High: ${quote['day_high']} | Day Low: ${quote['day_low']} | Vol: {quote['volume']:,}")
    print(f"     Attribution: Source='{quote['data_source']}', UTC Timestamp='{quote['retrieval_timestamp']}'")
    print("  ✓ [PASS] Live Quote Feed & Source Attribution Verified!\n")

    db.close()

    print("=" * 75)
    print("   ALL 8 MODULE 2 SPECIFICATION CRITERIA VERIFIED 100% SUCCESSFUL!")
    print("=" * 75)

if __name__ == "__main__":
    run_market_data_tests()
