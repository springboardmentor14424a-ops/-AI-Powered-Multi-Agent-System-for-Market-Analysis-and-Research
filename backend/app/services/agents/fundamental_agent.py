"""
Fundamental Analysis Agent.
Analyzes company revenue, profit, EPS, debt, and key financial ratios.
Identifies strengths & weaknesses and generates a comprehensive financial health report
using Google Gemini API (with deterministic financial heuristics fallback).
"""

from typing import Dict, Any, List
import logging
from app.services.ratio_service import fetch_and_calculate_real_financial_ratios
from app.schemas.agent_schemas import (
    FundamentalAnalysisResponse,
    FundamentalRatios,
)
from app.services.gemini_service import generate_gemini_content

logger = logging.getLogger(__name__)


def run_fundamental_analysis(symbol: str) -> FundamentalAnalysisResponse:
    """
    Executes fundamental analysis for a given stock symbol.
    """
    raw_data = fetch_and_calculate_real_financial_ratios(symbol)
    
    ratios_dict = raw_data.get("ratios", {})
    raw_metrics = raw_data.get("raw_metrics", {})
    company_name = raw_data.get("company_name", symbol)
    current_price = raw_data.get("current_price")
    
    pe = ratios_dict.get("pe_ratio")
    eps = ratios_dict.get("eps")
    roe = ratios_dict.get("roe")
    de = ratios_dict.get("debt_to_equity")
    cr = ratios_dict.get("current_ratio")
    npm = ratios_dict.get("net_profit_margin")
    roa = ratios_dict.get("roa")
    
    revenue = raw_metrics.get("total_revenue")
    net_income = raw_metrics.get("net_income")
    total_debt = raw_metrics.get("total_debt")

    # Assess Strengths and Weaknesses
    strengths: List[str] = []
    weaknesses: List[str] = []
    score = 50.0  # Base neutral score

    # ROE
    if roe is not None:
        if roe >= 15.0:
            strengths.append(f"High Return on Equity (ROE: {roe:.1f}%), indicating exceptional capital efficiency.")
            score += 10
        elif roe < 5.0:
            weaknesses.append(f"Subdued Return on Equity (ROE: {roe:.1f}%), indicating poor shareholder return.")
            score -= 8

    # Current Ratio (Liquidity)
    if cr is not None:
        if cr >= 1.5:
            strengths.append(f"Robust balance sheet liquidity with Current Ratio of {cr:.2f}x.")
            score += 8
        elif cr < 1.0:
            weaknesses.append(f"Short-term liquidity risk; Current Ratio of {cr:.2f}x indicates current liabilities exceed liquid assets.")
            score -= 10

    # Debt-to-Equity (Solvency)
    if de is not None:
        if de <= 0.8:
            strengths.append(f"Conservative capital structure with low Debt-to-Equity ratio ({de:.2f}x).")
            score += 9
        elif de > 2.0:
            weaknesses.append(f"Elevated debt burden; Debt-to-Equity of {de:.2f}x heightens solvency vulnerability.")
            score -= 9

    # Net Profit Margin
    if npm is not None:
        if npm >= 15.0:
            strengths.append(f"Solid profitability profile with Net Profit Margin of {npm:.1f}%.")
            score += 9
        elif npm < 0.0:
            weaknesses.append(f"Unprofitable operations; negative Net Profit Margin of {npm:.1f}%.")
            score -= 12
        elif npm < 5.0:
            weaknesses.append(f"Slim profit margins ({npm:.1f}%), making earnings sensitive to cost inflation.")
            score -= 4

    # EPS
    if eps is not None:
        if eps > 0:
            strengths.append(f"Positive profitability generating ${eps:.2f} Earnings Per Share.")
            score += 6
        else:
            weaknesses.append(f"Negative Earnings Per Share (${eps:.2f}), reflecting operating losses.")
            score -= 10

    # ROA
    if roa is not None:
        if roa >= 8.0:
            strengths.append(f"Efficient asset utilization with ROA of {roa:.1f}%.")
            score += 6
        elif roa < 2.0:
            weaknesses.append(f"Low asset turnover/productivity (ROA: {roa:.1f}%).")
            score -= 4

    # P/E Valuation
    if pe is not None:
        if pe < 15.0 and pe > 0:
            strengths.append(f"Attractive price valuation trading at {pe:.1f}x P/E ratio.")
            score += 5
        elif pe > 40.0:
            weaknesses.append(f"Premium valuation with P/E of {pe:.1f}x, pricing in aggressive growth expectations.")
            score -= 5

    # Clamp score
    financial_health_score = max(5.0, min(95.0, round(score, 1)))

    # Generate Health Summary
    if financial_health_score >= 70:
        health_tier = "Strong"
        summary_verdict = f"{company_name} demonstrates resilient balance sheet fundamentals, solid profitability, and sustainable operational efficiency."
    elif financial_health_score >= 45:
        health_tier = "Moderate"
        summary_verdict = f"{company_name} displays balanced fundamentals with stable core metrics, counterbalanced by moderate leverage or margin pressures."
    else:
        health_tier = "Vulnerable"
        summary_verdict = f"{company_name} faces fundamental headwinds regarding profitability, debt obligations, or working capital liquidity."

    rev_str = f"${revenue:,.0f}" if revenue is not None else "N/A"
    net_inc_str = f"${net_income:,.0f}" if net_income is not None else "N/A"
    debt_str = f"${total_debt:,.0f}" if total_debt is not None else "N/A"
    price_str = f"${current_price:.2f}" if current_price is not None else "N/A"
    eps_str = f"${eps:.2f}" if eps is not None else "N/A"
    roe_str = f"{roe:.1f}%" if roe is not None else "N/A"
    de_str = f"{de:.2f}x" if de is not None else "N/A"
    cr_str = f"{cr:.2f}x" if cr is not None else "N/A"
    npm_str = f"{npm:.1f}%" if npm is not None else "N/A"
    roa_str = f"{roa:.1f}%" if roa is not None else "N/A"
    pe_str = f"{pe:.1f}x" if pe is not None else "N/A"

    # Gemini API prompt for deep executive financial report
    prompt = f"""
You are a senior financial analyst. Provide an executive financial health report for {company_name} (Ticker: {symbol}).

Key Financial Metrics:
- Current Price: {price_str}
- Revenue: {rev_str}
- Net Income: {net_inc_str}
- Total Debt: {debt_str}
- P/E Ratio: {pe_str}
- EPS: {eps_str}
- ROE: {roe_str}
- Debt-to-Equity: {de_str}
- Current Ratio: {cr_str}
- Net Profit Margin: {npm_str}
- ROA: {roa_str}
- Overall Health Score: {financial_health_score}/100 ({health_tier})

Identified Strengths:
{chr(10).join('- ' + s for s in strengths) if strengths else 'None identified'}

Identified Weaknesses:
{chr(10).join('- ' + w for w in weaknesses) if weaknesses else 'None identified'}

Format your report into:
1. Executive Summary
2. Profitability & Operational Efficiency (ROE, Margin, ROA)
3. Balance Sheet Liquidity & Solvency (Debt/Equity, Current Ratio)
4. Valuation Context & Forward Outlook
Keep it concise, professional, and actionable.
"""
    system_instruction = "You are a Wall Street Chartered Financial Analyst (CFA) specializing in fundamental corporate balance sheet analysis."
    
    ai_report = generate_gemini_content(prompt=prompt, system_instruction=system_instruction)
    
    if not ai_report:
        # High quality fallback
        ai_report = f"""### Executive Financial Health Report: {company_name} ({symbol})

**Overall Health Classification:** {health_tier} ({financial_health_score}/100)

**1. Executive Summary**
{summary_verdict}

**2. Profitability & Operational Efficiency**
- Net Profit Margin: {npm_str}
- Return on Equity (ROE): {roe_str}
- Return on Assets (ROA): {roa_str}
- Diluted EPS: {eps_str}

**3. Balance Sheet Liquidity & Solvency**
- Current Ratio: {cr_str}
- Debt-to-Equity: {de_str}
- Total Reported Debt: {debt_str}

**4. Strategic Takeaways**
{"* " + chr(10) + "* ".join(strengths) if strengths else "* Capital position remains stable."}
{"* Caveats: " + chr(10) + "* ".join(weaknesses) if weaknesses else "* No critical balance sheet risks detected."}
"""

    return FundamentalAnalysisResponse(
        symbol=symbol,
        company_name=company_name,
        current_price=current_price,
        revenue=revenue,
        net_income=net_income,
        eps=eps,
        total_debt=total_debt,
        ratios=FundamentalRatios(
            pe_ratio=pe,
            eps=eps,
            roe=roe,
            debt_to_equity=de,
            current_ratio=cr,
            net_profit_margin=npm,
            roa=roa,
        ),
        strengths=strengths,
        weaknesses=weaknesses,
        financial_health_score=financial_health_score,
        financial_health_summary=summary_verdict,
        ai_generated_report=ai_report,
    )
