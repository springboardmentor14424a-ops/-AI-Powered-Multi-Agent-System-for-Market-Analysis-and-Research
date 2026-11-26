"""
Technical Analysis Agent.
Analyzes historical stock prices, calculates SMA (20, 50, 200), EMA (12, 26, 50),
RSI (14), and MACD, identifies bullish and bearish signals, and generates interactive charts.
"""

from typing import Dict, Any, List
import logging
import yfinance as yf
import pandas as pd
from app.services.indicators import (
    compute_all_technical_indicators,
    generate_interactive_stock_chart_plotly,
)
from app.schemas.agent_schemas import (
    TechnicalAnalysisResponse,
    TechnicalIndicatorsSummary,
)

logger = logging.getLogger(__name__)


def run_technical_analysis(symbol: str) -> TechnicalAnalysisResponse:
    """
    Executes technical analysis on 1-year historical price data.
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y", interval="1d")
    
    if df.empty or len(df) < 20:
        raise ValueError(f"Insufficient historical price data available for symbol '{symbol}'.")

    # Reset index and format columns
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    if "date" in df.columns and hasattr(df["date"], "dt"):
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    elif "datetime" in df.columns and hasattr(df["datetime"], "dt"):
        df["date"] = df["datetime"].dt.strftime("%Y-%m-%d")

    # Calculate indicators
    enriched = compute_all_technical_indicators(df)
    
    latest = enriched.iloc[-1]
    prev = enriched.iloc[-2] if len(enriched) > 1 else latest

    close = float(latest["close"])
    sma_20 = float(latest["sma_20"]) if pd.notnull(latest.get("sma_20")) else None
    sma_50 = float(latest["sma_50"]) if pd.notnull(latest.get("sma_50")) else None
    sma_200 = float(latest["sma_200"]) if pd.notnull(latest.get("sma_200")) else None

    ema_12 = float(latest["ema_12"]) if pd.notnull(latest.get("ema_12")) else None
    ema_26 = float(latest["ema_26"]) if pd.notnull(latest.get("ema_26")) else None
    ema_50 = float(latest["ema_50"]) if pd.notnull(latest.get("ema_50")) else None

    rsi_14 = float(latest["rsi_14"]) if pd.notnull(latest.get("rsi_14")) else None
    macd = float(latest["macd"]) if pd.notnull(latest.get("macd")) else None
    macd_signal = float(latest["macd_signal"]) if pd.notnull(latest.get("macd_signal")) else None
    macd_hist = float(latest["macd_hist"]) if pd.notnull(latest.get("macd_hist")) else None

    prev_macd = float(prev["macd"]) if pd.notnull(prev.get("macd")) else None
    prev_signal = float(prev["macd_signal"]) if pd.notnull(prev.get("macd_signal")) else None

    bullish_signals: List[str] = []
    bearish_signals: List[str] = []
    neutral_signals: List[str] = []
    score = 0.0  # -100 to +100

    # 1. Moving Average Price Alignment
    if sma_20 and close > sma_20:
        bullish_signals.append(f"Price (${close:.2f}) is trading above short-term 20-day SMA (${sma_20:.2f}).")
        score += 15
    elif sma_20:
        bearish_signals.append(f"Price (${close:.2f}) is trading below short-term 20-day SMA (${sma_20:.2f}).")
        score -= 15

    if sma_50 and sma_200:
        if sma_50 > sma_200:
            bullish_signals.append(f"Golden Cross condition confirmed: 50-day SMA (${sma_50:.2f}) > 200-day SMA (${sma_200:.2f}).")
            score += 25
        else:
            bearish_signals.append(f"Death Cross condition: 50-day SMA (${sma_50:.2f}) < 200-day SMA (${sma_200:.2f}).")
            score -= 25

    # 2. Short-term EMA Momentum
    if ema_12 and ema_26:
        if ema_12 > ema_26:
            bullish_signals.append(f"Fast EMA(12) (${ema_12:.2f}) is above Slow EMA(26) (${ema_26:.2f}), signaling bullish momentum.")
            score += 15
        else:
            bearish_signals.append(f"Fast EMA(12) (${ema_12:.2f}) is below Slow EMA(26) (${ema_26:.2f}), signaling bearish momentum.")
            score -= 15

    # 3. RSI Evaluation
    if rsi_14 is not None:
        if rsi_14 >= 70:
            bearish_signals.append(f"RSI(14) is at {rsi_14:.1f} (Overbought territory, elevated risk of consolidation or pullback).")
            score -= 15
        elif rsi_14 <= 30:
            bullish_signals.append(f"RSI(14) is at {rsi_14:.1f} (Oversold territory, potential bullish reversal / bounce opportunity).")
            score += 20
        elif 50 <= rsi_14 < 70:
            bullish_signals.append(f"RSI(14) is healthy at {rsi_14:.1f}, indicating positive buying pressure.")
            score += 10
        else:
            bearish_signals.append(f"RSI(14) is soft at {rsi_14:.1f}, indicating prevailing selling pressure.")
            score -= 10

    # 4. MACD Crossover and Histogram
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            bullish_signals.append(f"MACD Line ({macd:.3f}) is above Signal Line ({macd_signal:.3f}).")
            score += 15
            if prev_macd is not None and prev_signal is not None and prev_macd <= prev_signal:
                bullish_signals.append("Fresh Bullish MACD Crossover occurred.")
                score += 10
        else:
            bearish_signals.append(f"MACD Line ({macd:.3f}) is below Signal Line ({macd_signal:.3f}).")
            score -= 15
            if prev_macd is not None and prev_signal is not None and prev_macd >= prev_signal:
                bearish_signals.append("Fresh Bearish MACD Crossover occurred.")
                score -= 10

    # Determine Overall Signal
    clamped_score = max(-100.0, min(100.0, round(score, 1)))
    if clamped_score >= 45:
        overall_signal = "Strong Buy"
    elif clamped_score >= 15:
        overall_signal = "Buy"
    elif clamped_score <= -45:
        overall_signal = "Strong Sell"
    elif clamped_score <= -15:
        overall_signal = "Sell"
    else:
        overall_signal = "Neutral"

    rsi_str = f"{rsi_14:.1f}" if rsi_14 is not None else "N/A"
    macd_hist_str = f"{macd_hist:+.3f}" if macd_hist is not None else "0.000"

    summary_text = (
        f"{symbol} technical setup is currently {overall_signal} (Signal Score: {clamped_score:+.0f}). "
        f"Key drivers: {len(bullish_signals)} bullish indicator(s) vs {len(bearish_signals)} bearish indicator(s). "
        f"RSI is at {rsi_str} with MACD histogram at {macd_hist_str}."
    )

    # Generate interactive Plotly JSON
    chart_json = generate_interactive_stock_chart_plotly(enriched, symbol)

    return TechnicalAnalysisResponse(
        symbol=symbol,
        current_price=close,
        indicators=TechnicalIndicatorsSummary(
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_12=ema_12,
            ema_26=ema_26,
            ema_50=ema_50,
            rsi_14=rsi_14,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
        ),
        bullish_signals=bullish_signals,
        bearish_signals=bearish_signals,
        neutral_signals=neutral_signals,
        overall_signal=overall_signal,
        signal_score=clamped_score,
        summary=summary_text,
        chart_json=chart_json,
    )
