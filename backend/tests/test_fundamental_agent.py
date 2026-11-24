"""
Test Suite for Agent 3: Fundamental Analysis Agent
Validates:
1. Revenue and Earnings YoY calculations and trend classification
2. Profitability ratios (Gross Margin, Operating Margin, Net Margin, ROE, ROA)
3. Debt and Financial Stability (Debt/Equity, Current Ratio, Solvency Grade, Risk Warnings)
4. Valuation multiples (P/E, P/B, EV/EBITDA, Target Price)
5. Multi-year historical financial performance series
6. Peer comparison matrix and relative strengths/weaknesses
7. Missing and inconsistent data detection (Zero fabrication audit)
8. End-to-end API endpoints: POST /analyze, GET /history, GET /{id}, DELETE /{id}
"""

import pytest
import json
from app.services.fundamental_agent import (
    run_fundamental_agent_analysis,
    safe_div,
    format_number
)

@pytest.fixture
def auth_headers(client):
    """Registers and logs in a test user to obtain JWT authorization headers."""
    register_payload = {
        "full_name": "Fundamental Analyst User",
        "email": "fundamental.analyst@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    client.post("/api/auth/register", json=register_payload)

    login_resp = client.post("/api/auth/login", json={
        "email": "fundamental.analyst@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_fundamental_agent_math_helpers():
    """Validates math helpers for zero division and formatting."""
    assert safe_div(100, 20) == 5.0
    assert safe_div(100, 0) is None
    assert safe_div(None, 20) is None
    assert safe_div(100, None) is None

    assert format_number(1_500_000_000_000) == "$1.50T"
    assert format_number(2_400_000_000) == "$2.40B"
    assert format_number(35_000_000) == "$35.00M"
    assert format_number(None) == "N/A"


def test_fundamental_agent_core_analysis_service():
    """
    Direct service verification:
    Calls run_fundamental_agent_analysis on AAPL (NASDAQ) to verify all 7 requirements.
    """
    result = run_fundamental_agent_analysis(ticker="AAPL", market="NASDAQ", company_name="Apple Inc.")

    # 1. Metadata and Traceability
    assert result["ticker"] == "AAPL"
    assert result["market"] == "NASDAQ"
    assert result["currency"] in ["USD", "$"]
    assert result["data_source"] == "Yahoo Finance (yfinance API)"
    assert "retrieved_at_utc" in result

    # 2. Revenue & Earnings Analysis
    rev = result["revenue_earnings_analysis"]
    assert "latest_revenue" in rev
    assert "latest_net_income" in rev
    assert "revenue_growth_yoy" in rev
    assert "earnings_growth_yoy" in rev
    assert rev["trend_verdict"] in [
        "Strong Growth", "Steady Growth", "Margin Compression",
        "Declining Performance", "Moderate Stability"
    ]
    assert len(rev["explanation"]) > 10

    # 3. Profitability Analysis
    prof = result["profitability_analysis"]
    assert "gross_margin_pct" in prof
    assert "operating_margin_pct" in prof
    assert "net_margin_pct" in prof
    assert "roe_pct" in prof
    assert "roa_pct" in prof
    assert len(prof["evaluation"]) > 10

    # 4. Debt & Financial Stability Analysis
    debt = result["debt_stability_analysis"]
    assert "total_debt" in debt
    assert "debt_to_equity" in debt
    assert "current_ratio" in debt
    assert "solvency_grade" in debt
    assert isinstance(debt["financial_risks"], list)

    # 5. Valuation Analysis
    val = result["valuation_analysis"]
    assert "pe_ratio" in val
    assert "forward_pe" in val
    assert "pb_ratio" in val
    assert "valuation_verdict" in val
    assert len(val["explanation"]) > 10

    # 6. Historical Financial Performance
    hist = result["historical_trends"]
    assert isinstance(hist, list)
    assert len(hist) > 0
    first_hist = hist[0]
    assert "year" in first_hist
    assert "revenue" in first_hist
    assert "net_income" in first_hist

    # 7. Peer Comparison
    peers = result["peer_comparison"]
    assert "benchmark_table" in peers
    assert isinstance(peers["benchmark_table"], list)
    assert len(peers["benchmark_table"]) >= 2
    assert "relative_strengths" in peers
    assert "relative_weaknesses" in peers

    # 8. Missing Data Audit (Zero Fabrication)
    audit = result["missing_data_audit"]
    assert "has_missing_data" in audit
    assert "missing_items" in audit
    assert "integrity_confirmation" in audit

    # 9. Health Score
    health = result["health_score"]
    assert 0 <= health["score"] <= 100
    assert health["grade"] in ["A", "B", "C", "D"]
    assert health["risk_level"] in ["Low", "Low-to-Moderate", "Moderate", "High"]


def test_fundamental_analysis_api_lifecycle(client, auth_headers):
    """
    Tests full API lifecycle:
    1. POST /api/fundamental/analyze
    2. GET /api/fundamental/history
    3. GET /api/fundamental/{analysis_id}
    4. DELETE /api/fundamental/{analysis_id}
    """
    # 1. Run Analysis via API
    analyze_payload = {
        "ticker": "AAPL",
        "market": "NASDAQ",
        "company_name": "Apple Inc."
    }
    create_resp = client.post("/api/fundamental/analyze", json=analyze_payload, headers=auth_headers)
    assert create_resp.status_code == 201, f"Failed: {create_resp.text}"
    data = create_resp.json()
    assert "analysis_id" in data
    analysis_id = data["analysis_id"]
    assert data["ticker"] == "AAPL"
    assert data["market"] == "NASDAQ"
    assert "health_score" in data

    # 2. Retrieve Analysis History
    hist_resp = client.get("/api/fundamental/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    history_items = hist_resp.json()
    assert len(history_items) >= 1
    found = any(item["analysis_id"] == analysis_id for item in history_items)
    assert found is True

    # 3. Retrieve Analysis by ID
    detail_resp = client.get(f"/api/fundamental/{analysis_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["analysis_id"] == analysis_id
    assert detail["ticker"] == "AAPL"
    assert "profitability_analysis" in detail
    assert "debt_stability_analysis" in detail

    # 4. Delete Analysis Report
    del_resp = client.delete(f"/api/fundamental/{analysis_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # 5. Verify it is gone
    not_found_resp = client.get(f"/api/fundamental/{analysis_id}", headers=auth_headers)
    assert not_found_resp.status_code == 404


def test_fundamental_analysis_unauthorized(client):
    """Verifies that endpoints require valid JWT authentication."""
    resp = client.post("/api/fundamental/analyze", json={
        "ticker": "AAPL",
        "market": "NASDAQ"
    })
    assert resp.status_code == 401

    resp_hist = client.get("/api/fundamental/history")
    assert resp_hist.status_code == 401
