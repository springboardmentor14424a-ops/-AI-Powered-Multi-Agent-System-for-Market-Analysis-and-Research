"""
FastAPI Router for Autonomous Stock Analysis Agents:
- Fundamental Analysis Agent
- Technical Analysis Agent
- News & Sentiment Agent
- Risk Analysis Agent
- Unified Multi-Agent Synthesis
"""

from fastapi import APIRouter, HTTPException, Path
from app.schemas.agent_schemas import (
    FundamentalAnalysisResponse,
    TechnicalAnalysisResponse,
    NewsSentimentResponse,
    RiskAnalysisResponse,
    MultiAgentSummaryResponse,
    _normalize_symbol,
)
from app.services.agents.fundamental_agent import run_fundamental_analysis
from app.services.agents.technical_agent import run_technical_analysis
from app.services.agents.news_agent import run_news_sentiment_analysis
from app.services.agents.risk_agent import run_risk_analysis
from app.services.agents.master_agent import run_full_multi_agent_analysis

router = APIRouter(prefix="/api/agents", tags=["ai-agents"])


@router.get("/{symbol}/fundamental", response_model=FundamentalAnalysisResponse)
def get_fundamental_analysis(
    symbol: str = Path(..., description="Stock ticker symbol (e.g. AAPL, MSFT)")
):
    """
    Fundamental Analysis Agent:
    Analyzes company revenue, profit, EPS, debt and financial ratios.
    Identifies financial strengths and weaknesses.
    Generates a company financial health report with Gemini AI.
    """
    try:
        norm_sym = _normalize_symbol(symbol)
        return run_fundamental_analysis(norm_sym)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fundamental analysis failed: {str(exc)}")


@router.get("/{symbol}/technical", response_model=TechnicalAnalysisResponse)
def get_technical_analysis(
    symbol: str = Path(..., description="Stock ticker symbol (e.g. AAPL, MSFT)")
):
    """
    Technical Analysis Agent:
    Analyzes historical prices using SMA (20, 50, 200), EMA (12, 26, 50), RSI (14), and MACD.
    Identifies bullish and bearish signals.
    Generates an interactive Plotly technical chart.
    """
    try:
        norm_sym = _normalize_symbol(symbol)
        return run_technical_analysis(norm_sym)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Technical analysis failed: {str(exc)}")


@router.get("/{symbol}/news-sentiment", response_model=NewsSentimentResponse)
def get_news_sentiment_analysis(
    symbol: str = Path(..., description="Stock ticker symbol (e.g. AAPL, MSFT)")
):
    """
    News & Sentiment Agent:
    Retrieves real-time financial news via Finnhub/market feeds (headlines, summaries, source, URL, date).
    Classifies news as Positive, Negative or Neutral with sentiment scores.
    Generates an executive news summary with Gemini AI.
    """
    try:
        norm_sym = _normalize_symbol(symbol)
        return run_news_sentiment_analysis(norm_sym)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"News & sentiment analysis failed: {str(exc)}")


@router.get("/{symbol}/risk", response_model=RiskAnalysisResponse)
def get_risk_analysis(
    symbol: str = Path(..., description="Stock ticker symbol (e.g. AAPL, MSFT)")
):
    """
    Risk Analysis Agent:
    Calculates stock volatility, beta (vs SPY), maximum drawdown, and standard deviation.
    Identifies financial and market risks.
    Generates a 0-100 risk score and classifies as Low, Moderate, or High.
    """
    try:
        norm_sym = _normalize_symbol(symbol)
        return run_risk_analysis(norm_sym)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(exc)}")


@router.get("/{symbol}/all", response_model=MultiAgentSummaryResponse)
def get_all_agents_analysis(
    symbol: str = Path(..., description="Stock ticker symbol (e.g. AAPL, MSFT)")
):
    """
    Full Multi-Agent Orchestration:
    Runs all 4 analysis agents independently and returns a validated institutional synthesis.
    """
    try:
        norm_sym = _normalize_symbol(symbol)
        return run_full_multi_agent_analysis(norm_sym)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multi-agent synthesis failed: {str(exc)}")
