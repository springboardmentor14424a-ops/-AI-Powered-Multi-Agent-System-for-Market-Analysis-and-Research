import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
os.environ["ENABLE_LIVE_FINANCE_API"] = "0"
import time
from app.database import Base, engine, SessionLocal
from app.routers.market_data import get_fundamental_analysis, audit_custom_fundamental_data
from app.schemas import FundamentalAuditRequest


def run_fundamental_agent_tests():
    print("=" * 75)
    print("   MODULE 3: FUNDAMENTAL ANALYSIS AGENT - VERIFICATION SUITE")
    print("=" * 75)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 75)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear cached financials for clean re-generation with calibrated model
    from app.models import CompanyFinancial
    db.query(CompanyFinancial).delete()
    db.commit()

    # ---------------------------------------------------------
    # TEST 1: FULL FUNDAMENTAL ANALYSIS ON US TECH (AAPL)
    # ---------------------------------------------------------
    print("\n[TEST 1] ANALYZING AAPL (NASDAQ) — REVENUE, PROFITABILITY, DEBT, RATIOS...")
    aapl = get_fundamental_analysis(ticker="AAPL", market="NASDAQ", period_type="annual", db=db)

    assert aapl["ticker"] == "AAPL"
    assert aapl["revenue_and_earnings"]["latest_yoy_revenue_growth_pct"] is not None
    assert aapl["profitability"]["gross_margin_pct"] > 40
    assert aapl["debt_and_stability"]["current_ratio"] > 0
    assert aapl["pe_ratio"] != "N/A"
    assert aapl["pb_ratio"] != "N/A"
    assert aapl["roe"] != "N/A"
    assert len(aapl["historical_comparison"]) == 4
    assert len(aapl["peer_comparison"]["peers"]) >= 2
    assert aapl["data_quality_audit"]["completeness_score_pct"] == 100.0
    assert aapl["data_quality_audit"]["is_consistent"] is True

    print(f"  -> Company: {aapl['company_name']} | Health: {aapl['health']} | Verdict: {aapl['valuation_status']}")
    print(f"  -> Revenue & Earnings: {aapl['revenue_and_earnings']['latest_yoy_revenue_growth_display']} (CAGR: {aapl['revenue_and_earnings']['revenue_cagr_pct']}%)")
    print(f"  -> Profitability: Gross={aapl['profitability']['gross_margin_pct']}%, Operating={aapl['profitability']['operating_margin_pct']}%, Net={aapl['profitability']['net_margin_display']}")
    print(f"  -> Debt & Stability: D/E={aapl['debt_and_stability']['debt_to_equity']}, Current Ratio={aapl['debt_and_stability']['current_ratio']}x ({aapl['debt_and_stability']['stability_rating']})")
    print(f"  -> Ratios: P/E={aapl['pe_ratio']}, P/B={aapl['pb_ratio']}, ROE={aapl['roe']}, ROA={aapl['valuation_ratios']['roa']}")
    print(f"  -> Peers: {[p['ticker'] for p in aapl['peer_comparison']['peers']]} | {aapl['peer_comparison']['relative_valuation_verdict']}")
    print("  ✓ [PASS] AAPL Full Fundamental Analysis Verified!\n")

    # ---------------------------------------------------------
    # TEST 2: FULL FUNDAMENTAL ANALYSIS ON INDIAN EQUITY (TCS)
    # ---------------------------------------------------------
    print("[TEST 2] ANALYZING TCS (NSE) — HISTORICAL & PEER COMPARISON...")
    tcs = get_fundamental_analysis(ticker="TCS", market="NSE", period_type="annual", db=db)

    assert tcs["ticker"] == "TCS"
    assert tcs["currency"] == "INR"
    assert len(tcs["historical_comparison"]) == 4
    peer_tickers = [p["ticker"] for p in tcs["peer_comparison"]["peers"]]
    assert "INFY" in peer_tickers or "WIPRO" in peer_tickers
    print(f"  -> TCS (NSE) Peers: {peer_tickers} | {tcs['peer_comparison']['relative_valuation_verdict']}")
    print(f"  -> Historical Revenue Trajectory: {[(r['period'], r['revenue']) for r in tcs['historical_comparison']]}")
    print("  ✓ [PASS] TCS Historical & Peer Comparison Verified!\n")

    # ---------------------------------------------------------
    # TEST 3: MISSING & INCONSISTENT FINANCIAL INFORMATION AUDIT
    # ---------------------------------------------------------
    print("[TEST 3] TESTING MISSING & INCONSISTENT FINANCIAL DATA DETECTION...")
    corrupt_payload = FundamentalAuditRequest(
        ticker="BROKEN-CORP",
        market="NYSE",
        current_price=120.0,
        profile={"name": "Broken Corp", "sector": None, "market_cap": None, "pe_ratio": None},
        financials={
            "currency": "USD",
            "income_statement": [
                {
                    "period": "FY 2025",
                    "total_revenue": 1000.0,
                    "cost_of_revenue": 400.0,
                    "gross_profit": 999.0,  # Inconsistent: 1000 - 400 != 999
                    "operating_income": 200.0,
                    "ebitda": 250.0,
                    "net_income": 150.0,
                    "eps": None,  # Missing EPS -> P/E should be N/A
                }
            ],
            "balance_sheet": [
                {
                    "period": "FY 2025",
                    "total_assets": 5000.0,
                    "total_liabilities": 2000.0,
                    "stockholders_equity": -100.0,  # Negative equity + Assets != Liab + Equity
                    "current_assets": 1000.0,
                    "current_liabilities": 800.0,
                    "long_term_debt": 1200.0,
                    "cash_and_equivalents": 300.0,
                }
            ],
            "cash_flow": [
                {
                    "period": "FY 2025",
                    "operating_cash_flow": 300.0,
                    "capital_expenditures": 100.0,
                    "free_cash_flow": 50.0,  # Inconsistent: 300 - 100 != 50
                }
            ],
        },
    )

    audit_res = audit_custom_fundamental_data(corrupt_payload)
    audit = audit_res["data_quality_audit"]

    assert audit["has_missing_data"] is True
    assert audit["is_consistent"] is False
    assert len(audit["missing_fields"]) >= 4
    assert len(audit["inconsistencies_found"]) >= 3
    assert audit_res["pe_ratio"] == "N/A"
    assert audit_res["roe"] == "N/A"

    print(f"  -> Completeness Score: {audit['completeness_score_pct']}%")
    print(f"  -> Missing Fields Detected ({len(audit['missing_fields'])}): {audit['missing_fields'][:3]}")
    print(f"  -> Inconsistencies Detected ({len(audit['inconsistencies_found'])}):")
    for inc in audit["inconsistencies_found"]:
        print(f"     • {inc}")
    print(f"  -> Graceful Ratio Handling: P/E={audit_res['pe_ratio']}, ROE={audit_res['roe']}")
    print("  ✓ [PASS] Missing & Inconsistent Financial Information Detection Verified!\n")

    db.close()
    print("=" * 75)
    print("   ALL MODULE 3 FUNDAMENTAL ANALYSIS AGENT TESTS PASSED 100%!")
    print("=" * 75)


if __name__ == "__main__":
    run_fundamental_agent_tests()
