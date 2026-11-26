"""
Risk Analysis Agent.
Calculates stock volatility (annualized), beta (vs S&P 500 SPY),
maximum drawdown (peak-to-trough), and daily/annualized standard deviation.
Identifies key financial and market risks and computes a composite 0-100 risk score.
"""

from typing import List, Optional
import math
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from app.schemas.agent_schemas import RiskAnalysisResponse

logger = logging.getLogger(__name__)


def calculate_max_drawdown(prices: pd.Series) -> float:
    """
    Calculates the maximum drawdown percentage:
    Max Drawdown = (Price - Running Max Price) / Running Max Price * 100
    Returns a negative percentage or 0.0.
    """
    if prices.empty or len(prices) < 2:
        return 0.0
    
    running_max = prices.cummax()
    drawdowns = (prices - running_max) / running_max * 100.0
    max_dd = float(drawdowns.min())
    return round(max_dd, 2)


def calculate_beta(stock_returns: pd.Series, benchmark_returns: pd.Series) -> Optional[float]:
    """
    Beta = Covariance(Stock Returns, Benchmark Returns) / Variance(Benchmark Returns)
    """
    combined = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
    if len(combined) < 20:
        return None
    
    cov = combined.iloc[:, 0].cov(combined.iloc[:, 1])
    benchmark_var = combined.iloc[:, 1].var()
    
    if benchmark_var == 0 or np.isnan(cov) or np.isnan(benchmark_var):
        return None
    
    beta = cov / benchmark_var
    return round(float(beta), 2)


def run_risk_analysis(symbol: str) -> RiskAnalysisResponse:
    """
    Executes quantitative risk assessment for the given stock.
    """
    # Fetch 1 year of daily data for target stock and SPY benchmark
    ticker = yf.Ticker(symbol)
    stock_hist = ticker.history(period="1y", interval="1d")
    
    if stock_hist.empty or len(stock_hist) < 20:
        raise ValueError(f"Insufficient historical data to conduct risk assessment for '{symbol}'.")

    stock_closes = stock_hist["Close"].dropna()
    stock_returns = stock_closes.pct_change().dropna()

    # Calculate Standard Deviations
    daily_std = float(stock_returns.std() * 100.0)  # in %
    annualized_volatility = float(stock_returns.std() * math.sqrt(252) * 100.0)  # in %

    # Maximum Drawdown
    max_dd = calculate_max_drawdown(stock_closes)

    # Calculate Beta vs SPY
    beta: Optional[float] = None
    try:
        spy_ticker = yf.Ticker("SPY")
        spy_hist = spy_ticker.history(period="1y", interval="1d")
        if not spy_hist.empty:
            spy_closes = spy_hist["Close"].dropna()
            spy_returns = spy_closes.pct_change().dropna()
            beta = calculate_beta(stock_returns, spy_returns)
    except Exception as e:
        logger.warning(f"Error fetching benchmark SPY data for beta: {e}")

    # Risk Factor Identification
    market_risks: List[str] = []
    risk_points = 30.0  # Base market exposure

    # Volatility scoring
    if annualized_volatility > 45.0:
        market_risks.append(f"Elevated price volatility: Annualized volatility of {annualized_volatility:.1f}% exceeds high-risk threshold (45%).")
        risk_points += 25
    elif annualized_volatility > 28.0:
        market_risks.append(f"Moderate price volatility: Annualized volatility sits at {annualized_volatility:.1f}%.")
        risk_points += 15
    else:
        risk_points += 5

    # Beta scoring
    if beta is not None:
        if beta > 1.5:
            market_risks.append(f"High systematic risk (Beta: {beta:.2f}x): Stock amplifies broader market swings significantly.")
            risk_points += 20
        elif beta > 1.15:
            market_risks.append(f"Above-average systematic market sensitivity (Beta: {beta:.2f}x).")
            risk_points += 10
        elif beta < 0.8:
            risk_points -= 8  # Defensive stock attribute
    else:
        market_risks.append("Benchmark beta unavailable; risk estimated primarily from idiosyncratic volatility.")

    # Max Drawdown scoring
    if max_dd < -35.0:
        market_risks.append(f"Severe drawdown vulnerability: Peak-to-trough decline reached {max_dd:.1f}% over the past year.")
        risk_points += 25
    elif max_dd < -20.0:
        market_risks.append(f"Moderate drawdown exposure: 1-year max drawdown of {max_dd:.1f}%.")
        risk_points += 15
    else:
        risk_points += 5

    # Composite Risk Score (0 to 100)
    risk_score = max(5.0, min(95.0, round(risk_points, 1)))

    if risk_score >= 65.0:
        risk_level = "High"
    elif risk_score >= 40.0:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    summary_text = (
        f"{symbol} is classified as {risk_level} Risk (Risk Score: {risk_score:.0f}/100). "
        f"The stock exhibits an annualized volatility of {annualized_volatility:.1f}%, a maximum drawdown of {max_dd:.1f}%, "
        f"and a market beta of {f'{beta:.2f}x' if beta is not None else 'N/A'}. "
        f"{'Cautious position sizing recommended.' if risk_level == 'High' else 'Standard risk management applies.'}"
    )

    return RiskAnalysisResponse(
        symbol=symbol,
        volatility_annualized=round(annualized_volatility, 2),
        beta=beta,
        max_drawdown=max_dd,
        standard_deviation_daily=round(daily_std, 2),
        standard_deviation_annualized=round(annualized_volatility, 2),
        risk_score=risk_score,
        risk_level=risk_level,
        market_risks=market_risks,
        summary=summary_text,
    )
