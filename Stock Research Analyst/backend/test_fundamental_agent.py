import asyncio
from database.connection import AsyncSessionLocal
from routers.fundamental_agent import analyze_company_fundamentals

async def test():
    async with AsyncSessionLocal() as session:
        for sym, mkt in [('RELIANCE.NS', 'NSE'), ('TCS.NS', 'NSE'), ('AAPL', 'NASDAQ')]:
            res = await analyze_company_fundamentals(sym, market=mkt, db=session)
            cname = res['company_name']
            print(f"\n=== {sym} ({cname}) ===")
            rev = res['revenue_and_earnings_analysis']
            print(f"  1. Revenue/Earnings : Rev={rev['total_revenue']} | YoY={rev['revenue_yoy_growth_pct']}% | NetInc={rev['net_income']} | {rev['earnings_status']}")
            prof = res['profitability_analysis']
            print(f"  2. Profitability    : Range={prof['profitability_range']} | GrossM={prof['gross_margin_pct']}% | OpM={prof['operating_margin_pct']}% | NetM={prof['net_profit_margin_pct']}% | ROE={prof['roe_pct']}%")
            debt = res['debt_and_financial_stability_analysis']
            print(f"  3. Debt & Stability : {debt['stability_category']} (Score={debt['financial_stability_score']}) | D/E={debt['debt_to_equity_ratio']} | D/A={debt['debt_to_assets_ratio']}")
            rat = res['financial_ratios_calculation']
            print(f"  4. Financial Ratios : P/E={rat['pe_ratio']} | FwdPE={rat['forward_pe']} | P/B={rat['pb_ratio']} | ROE={rat['roe_pct']}% | {rat['valuation_tier']} | Missing={rat['missing_ratio_inputs']}")
            hist = res['historical_financial_performance_comparison']
            print(f"  5. Historical Comp  : Years={hist['fiscal_years_compared']} | PriceRet1Y={hist['period_price_return_pct']}% | MaxDD={hist['period_max_drawdown_pct']}% | {hist['performance_tier']}")
            peer = res['peer_comparison']
            print(f"  6. Peer Comparison  : {peer['comparison_status']} | Avg={peer['peer_average']} | Unavail={peer['unavailable_or_missing_peers']}")
            dq = res['missing_or_inconsistent_financial_info']
            print(f"  7. Data Quality     : {dq['data_completeness_pct']}% ({dq['reliability_status']}) | Missing={dq['missing_fields_count']} | Inconsistencies={dq['inconsistencies_count']}")
            ml = res['ml_agent_prediction']
            print(f"  8. ML Verdict       : {ml.get('model_name')} -> {ml.get('regime')} ({ml.get('confidence_score')}%) | {ml.get('recommendation')}")

if __name__ == '__main__':
    asyncio.run(test())
