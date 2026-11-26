"""
Unit tests for Autonomous Agents:
- Fundamental Analysis Agent
- Technical Analysis Agent
- News & Sentiment Agent
- Risk Analysis Agent
- Master Multi-Agent Aggregator
- FastAPI Endpoints
"""

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.agent_schemas import (
    _normalize_symbol,
    FundamentalAnalysisResponse,
    TechnicalAnalysisResponse,
    NewsSentimentResponse,
    RiskAnalysisResponse,
    MultiAgentSummaryResponse,
)
from app.services.agents.news_agent import _classify_sentiment_heuristic
from app.services.agents.risk_agent import calculate_max_drawdown, calculate_beta

client = TestClient(app)


def test_symbol_normalization():
    assert _normalize_symbol("aapl") == "AAPL"
    assert _normalize_symbol("  msft  ") == "MSFT"
    assert _normalize_symbol("brk.b") == "BRK.B"
    with pytest.raises(ValueError):
        _normalize_symbol("")
    with pytest.raises(ValueError):
        _normalize_symbol("$$$INVALID@@")


def test_max_drawdown_calculation():
    # Peak at 120, drops to 90 -> -25.0%
    prices = pd.Series([100.0, 120.0, 90.0, 110.0])
    dd = calculate_max_drawdown(prices)
    assert dd == -25.0

    # No drawdown (monotonic increase)
    up_prices = pd.Series([10.0, 20.0, 30.0, 40.0])
    assert calculate_max_drawdown(up_prices) == 0.0

    # Empty
    assert calculate_max_drawdown(pd.Series(dtype=float)) == 0.0


def test_beta_calculation():
    # Perfect correlation with identical returns -> beta = 1.0
    stock_ret = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02] * 5)
    bench_ret = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02] * 5)
    beta = calculate_beta(stock_ret, bench_ret)
    assert beta is not None
    assert pytest.approx(beta, 0.01) == 1.0

    # Double amplitude -> beta = 2.0
    double_stock = bench_ret * 2.0
    beta_double = calculate_beta(double_stock, bench_ret)
    assert pytest.approx(beta_double, 0.01) == 2.0


def test_news_sentiment_heuristic():
    pos_text = "Tech giant reports record profit surge and revenue beat, stock rallies."
    label, score = _classify_sentiment_heuristic(pos_text)
    assert label == "Positive"
    assert score > 0.0

    neg_text = "Company faces massive loss, layoffs warning, and heavy legal fine as earnings plunge."
    label_neg, score_neg = _classify_sentiment_heuristic(neg_text)
    assert label_neg == "Negative"
    assert score_neg < 0.0

    neutral_text = "Board meeting scheduled for next Thursday to discuss annual shareholder proxy."
    label_neu, score_neu = _classify_sentiment_heuristic(neutral_text)
    assert label_neu == "Neutral"
    assert score_neu == 0.0


def test_agent_endpoints_fastapi():
    # Test valid ticker AAPL
    symbol = "AAPL"

    # 1. Fundamental Agent Endpoint
    resp_fund = client.get(f"/api/agents/{symbol}/fundamental")
    assert resp_fund.status_code == 200
    fund_data = resp_fund.json()
    assert fund_data["symbol"] == "AAPL"
    assert "ratios" in fund_data
    assert "strengths" in fund_data
    assert "weaknesses" in fund_data
    assert 0 <= fund_data["financial_health_score"] <= 100
    assert "ai_generated_report" in fund_data

    # 2. Technical Agent Endpoint
    resp_tech = client.get(f"/api/agents/{symbol}/technical")
    assert resp_tech.status_code == 200
    tech_data = resp_tech.json()
    assert tech_data["symbol"] == "AAPL"
    assert tech_data["overall_signal"] in ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]
    assert "indicators" in tech_data
    assert "chart_json" in tech_data
    assert tech_data["chart_json"] is not None

    # 3. News & Sentiment Endpoint
    resp_news = client.get(f"/api/agents/{symbol}/news-sentiment")
    assert resp_news.status_code == 200
    news_data = resp_news.json()
    assert news_data["symbol"] == "AAPL"
    assert news_data["overall_sentiment"] in ["Positive", "Negative", "Neutral"]
    assert -1.0 <= news_data["overall_score"] <= 1.0
    assert "articles" in news_data
    if news_data["articles"]:
        first = news_data["articles"][0]
        assert "headline" in first
        assert "source" in first
        assert "url" in first
        assert "published_at" in first
        assert "sentiment" in first

    # 4. Risk Agent Endpoint
    resp_risk = client.get(f"/api/agents/{symbol}/risk")
    assert resp_risk.status_code == 200
    risk_data = resp_risk.json()
    assert risk_data["symbol"] == "AAPL"
    assert risk_data["risk_level"] in ["Low", "Moderate", "High"]
    assert 0 <= risk_data["risk_score"] <= 100
    assert "volatility_annualized" in risk_data
    assert "max_drawdown" in risk_data

    # 5. Full Multi-Agent Synthesis Endpoint
    resp_all = client.get(f"/api/agents/{symbol}/all")
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert all_data["symbol"] == "AAPL"
    assert "fundamental" in all_data
    assert "technical" in all_data
    assert "news_sentiment" in all_data
    assert "risk" in all_data
    assert "composite_verdict" in all_data
    assert "executive_summary" in all_data


def test_agent_endpoints_invalid_symbol():
    resp = client.get("/api/agents/$$$BAD/fundamental")
    assert resp.status_code == 400
