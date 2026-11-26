"""
Master Multi-Agent Synthesis Service.
Coordinates Fundamental, Technical, News & Sentiment, and Risk agents
to deliver a unified, validated institutional investment synthesis.
"""

from typing import Dict, Any
import logging
from app.schemas.agent_schemas import (
    MultiAgentSummaryResponse,
    FundamentalAnalysisResponse,
    TechnicalAnalysisResponse,
    NewsSentimentResponse,
    RiskAnalysisResponse,
)
from app.services.agents.fundamental_agent import run_fundamental_analysis
from app.services.agents.technical_agent import run_technical_analysis
from app.services.agents.news_agent import run_news_sentiment_analysis
from app.services.agents.risk_agent import run_risk_analysis
from app.services.gemini_service import generate_gemini_content

logger = logging.getLogger(__name__)


def run_full_multi_agent_analysis(symbol: str) -> MultiAgentSummaryResponse:
    """
    Executes all four individual analysis agents and synthesizes an executive verdict.
    """
    symbol = symbol.strip().upper()

    fundamental = run_fundamental_analysis(symbol)
    technical = run_technical_analysis(symbol)
    news = run_news_sentiment_analysis(symbol)
    risk = run_risk_analysis(symbol)

    # Composite Scoring (0 to 100)
    # Fundamental weight: 35%, Technical weight: 30%, News weight: 15%, Risk weight (inverted): 20%
    f_score = fundamental.financial_health_score  # 0 to 100
    t_score = (technical.signal_score + 100.0) / 2.0  # normalize -100..+100 to 0..100
    n_score = (news.overall_score + 1.0) * 50.0  # normalize -1.0..+1.0 to 0..100
    r_score = max(0.0, 100.0 - risk.risk_score)  # Lower risk gives higher safety score

    composite_score = round(
        0.35 * f_score +
        0.30 * t_score +
        0.15 * n_score +
        0.20 * r_score,
        1
    )

    if composite_score >= 75.0:
        composite_verdict = "Bullish Outperform"
    elif composite_score >= 60.0:
        composite_verdict = "Moderate Buy"
    elif composite_score >= 45.0:
        composite_verdict = "Neutral Hold"
    elif composite_score >= 30.0:
        composite_verdict = "Underperform / Cautious"
    else:
        composite_verdict = "Bearish Sell"

    # AI synthesis via Gemini or structured template
    prompt = f"""
You are the Chief Investment Officer synthesizing 4 specialized agent reports for {symbol}:

1. Fundamental Agent: Health Score {f_score:.0f}/100. Key strengths: {', '.join(fundamental.strengths[:2]) if fundamental.strengths else 'Stable'}. Weaknesses: {', '.join(fundamental.weaknesses[:2]) if fundamental.weaknesses else 'None'}.
2. Technical Agent: Signal is {technical.overall_signal} (Score: {technical.signal_score:+.0f}). RSI: {f'{technical.indicators.rsi_14:.1f}' if technical.indicators.rsi_14 is not None else 'N/A'}.
3. News & Sentiment Agent: Sentiment is {news.overall_sentiment} (Score: {news.overall_score:+.2f}). Headlines: {len(news.articles)} articles tracked.
4. Risk Agent: Risk is {risk.risk_level} (Volatility: {risk.volatility_annualized:.1f}%, Drawdown: {risk.max_drawdown:.1f}%).

Composite Rating: {composite_verdict} ({composite_score}/100).

Synthesize a sharp 3-sentence institutional conclusion:
- What is the bottom line investment thesis?
- What is the major catalyst or risk to watch?
- Actionable recommendation for an investor.
"""
    ai_exec_summary = generate_gemini_content(
        prompt=prompt,
        system_instruction="You are the CIO of a multi-asset quantitative hedge fund synthesizing agent insights."
    )

    if not ai_exec_summary:
        ai_exec_summary = (
            f"{symbol} holds an overall composite rating of '{composite_verdict}' with an institutional score of {composite_score:.1f}/100. "
            f"The company pairs a {fundamental.financial_health_score:.0f}/100 fundamental health profile with a '{technical.overall_signal}' technical posture "
            f"and {news.overall_sentiment.lower()} news sentiment ({news.overall_score:+.2f}). "
            f"Risk profile is classified as {risk.risk_level} ({risk.volatility_annualized:.1f}% annualized volatility). "
            f"Investors should calibrate position sizing according to their specific risk tolerance."
        )

    return MultiAgentSummaryResponse(
        symbol=symbol,
        fundamental=fundamental,
        technical=technical,
        news_sentiment=news,
        risk=risk,
        composite_verdict=composite_verdict,
        composite_score=composite_score,
        executive_summary=ai_exec_summary,
    )
