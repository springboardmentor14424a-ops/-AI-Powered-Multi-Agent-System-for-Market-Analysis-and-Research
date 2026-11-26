import pytest
import math
from app.services.ratio_service import (
    calculate_pe_ratio,
    calculate_eps,
    calculate_roe,
    calculate_debt_to_equity,
    calculate_current_ratio,
    calculate_net_profit_margin,
    calculate_roa,
    compute_all_financial_ratios,
    fetch_and_calculate_real_financial_ratios,
    FinancialRatioValidationError,
)


# =====================================================================
# Unit Tests for P/E Ratio
# =====================================================================

def test_calculate_pe_ratio_valid():
    assert calculate_pe_ratio(100.0, 5.0) == 20.0
    assert calculate_pe_ratio(150.0, 7.5) == 20.0


def test_calculate_pe_ratio_negative_eps_returns_none():
    # If company operates at a net loss (EPS <= 0), P/E is undefined / not meaningful
    assert calculate_pe_ratio(100.0, -2.5) is None
    assert calculate_pe_ratio(100.0, 0.0) is None


def test_calculate_pe_ratio_negative_price():
    with pytest.raises(FinancialRatioValidationError, match="Price cannot be negative"):
        calculate_pe_ratio(-50.0, 5.0)


def test_calculate_pe_ratio_invalid_types():
    with pytest.raises(FinancialRatioValidationError):
        calculate_pe_ratio("invalid", 5.0)
    with pytest.raises(FinancialRatioValidationError):
        calculate_pe_ratio(100.0, None)


# =====================================================================
# Unit Tests for EPS (Earnings Per Share)
# =====================================================================

def test_calculate_eps_valid():
    # $1,000,000 Net Income / 500,000 Shares = $2.00 EPS
    assert calculate_eps(1_000_000, 500_000) == 2.0
    # Negative net income yields negative EPS
    assert calculate_eps(-500_000, 250_000) == -2.0


def test_calculate_eps_zero_or_negative_shares():
    with pytest.raises(FinancialRatioValidationError, match="cannot be zero"):
        calculate_eps(1_000_000, 0)
    with pytest.raises(FinancialRatioValidationError, match="must be greater than zero"):
        calculate_eps(1_000_000, -100)


# =====================================================================
# Unit Tests for ROE (Return on Equity)
# =====================================================================

def test_calculate_roe_valid():
    # $20M Net Income / $100M Equity = 20%
    assert calculate_roe(20_000_000, 100_000_000, as_percentage=True) == 20.0
    assert calculate_roe(20_000_000, 100_000_000, as_percentage=False) == 0.2


def test_calculate_roe_negative_or_zero_equity():
    # Negative shareholder equity distorts ROE
    assert calculate_roe(10_000_000, 0) is None
    assert calculate_roe(10_000_000, -50_000_000) is None


# =====================================================================
# Unit Tests for Debt-to-Equity (D/E)
# =====================================================================

def test_calculate_debt_to_equity_valid():
    # $50M Debt / $100M Equity = 0.50
    assert calculate_debt_to_equity(50_000_000, 100_000_000) == 0.5
    # Zero debt is valid
    assert calculate_debt_to_equity(0, 100_000_000) == 0.0


def test_calculate_debt_to_equity_negative_inputs():
    with pytest.raises(FinancialRatioValidationError, match="Total debt cannot be negative"):
        calculate_debt_to_equity(-10_000, 100_000)
    assert calculate_debt_to_equity(50_000_000, -10_000_000) is None


# =====================================================================
# Unit Tests for Current Ratio
# =====================================================================

def test_calculate_current_ratio_valid():
    # $200M Current Assets / $100M Current Liabilities = 2.0
    assert calculate_current_ratio(200_000_000, 100_000_000) == 2.0


def test_calculate_current_ratio_zero_or_negative_liabilities():
    with pytest.raises(FinancialRatioValidationError, match="cannot be zero"):
        calculate_current_ratio(100_000_000, 0)
    with pytest.raises(FinancialRatioValidationError, match="cannot be negative"):
        calculate_current_ratio(100_000_000, -50_000_000)


# =====================================================================
# Unit Tests for Net Profit Margin
# =====================================================================

def test_calculate_net_profit_margin_valid():
    # $15M Net Income / $100M Revenue = 15%
    assert calculate_net_profit_margin(15_000_000, 100_000_000, as_percentage=True) == 15.0
    # Net Loss yields negative profit margin
    assert calculate_net_profit_margin(-5_000_000, 100_000_000, as_percentage=True) == -5.0


def test_calculate_net_profit_margin_zero_revenue():
    with pytest.raises(FinancialRatioValidationError, match="cannot be zero"):
        calculate_net_profit_margin(10_000_000, 0)


# =====================================================================
# Unit Tests for ROA (Return on Assets)
# =====================================================================

def test_calculate_roa_valid():
    # $10M Net Income / $100M Total Assets = 10%
    assert calculate_roa(10_000_000, 100_000_000, as_percentage=True) == 10.0
    assert calculate_roa(-4_000_000, 100_000_000, as_percentage=True) == -4.0


def test_calculate_roa_zero_or_negative_assets():
    with pytest.raises(FinancialRatioValidationError, match="cannot be zero"):
        calculate_roa(10_000_000, 0)
    with pytest.raises(FinancialRatioValidationError, match="Total assets must be positive"):
        calculate_roa(10_000_000, -500_000)


# =====================================================================
# Composite Ratios Calculation & Error Handling Test
# =====================================================================

def test_compute_all_financial_ratios_comprehensive():
    res = compute_all_financial_ratios(
        price=150.0,
        net_income=30_000_000,
        shares_outstanding=10_000_000,
        total_shareholder_equity=120_000_000,
        total_debt=60_000_000,
        current_assets=80_000_000,
        current_liabilities=40_000_000,
        total_revenue=200_000_000,
        total_assets=300_000_000,
    )
    ratios = res["ratios"]
    assert ratios["eps"] == 3.0
    assert ratios["pe_ratio"] == 50.0
    assert ratios["roe"] == 25.0
    assert ratios["debt_to_equity"] == 0.5
    assert ratios["current_ratio"] == 2.0
    assert ratios["net_profit_margin"] == 15.0
    assert ratios["roa"] == 10.0
    assert len(res["calculation_errors"]) == 0


def test_compute_all_financial_ratios_handles_missing_and_zero_values():
    # Handles missing values gracefully without crashing
    res = compute_all_financial_ratios(
        price=100.0,
        net_income=10_000,
        shares_outstanding=0, # Zero denominator
        total_revenue=0,      # Zero denominator
    )
    ratios = res["ratios"]
    assert ratios["eps"] is None
    assert ratios["pe_ratio"] is None
    assert "eps" in res["calculation_errors"]
    assert "net_profit_margin" in res["calculation_errors"]


# =====================================================================
# Real Financial Data Integration Test
# =====================================================================

def test_fetch_and_calculate_real_financial_ratios_aapl():
    data = fetch_and_calculate_real_financial_ratios("AAPL")
    assert data["symbol"] == "AAPL"
    r = data["financial_ratios"]
    
    # Verify all 7 ratios are present in the response
    for key in ["pe_ratio", "eps", "roe", "debt_to_equity", "current_ratio", "net_profit_margin", "roa"]:
        assert key in r
        assert "value" in r[key]
        assert "display" in r[key]
        assert "description" in r[key]

    # Apple (profitable company) should have positive EPS, ROA, Current Ratio, etc.
    assert r["eps"]["value"] is not None and r["eps"]["value"] > 0
    assert r["current_ratio"]["value"] is not None and r["current_ratio"]["value"] > 0
    assert r["net_profit_margin"]["value"] is not None and r["net_profit_margin"]["value"] > 0
