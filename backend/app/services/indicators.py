"""
Technical Indicators Engine.
Calculates:
- SMA (Simple Moving Average): 20, 50, 200 days
- EMA (Exponential Moving Average): 12, 26, 50 days
- RSI (Relative Strength Index): 14 days
- MACD (Moving Average Convergence Divergence): MACD line (EMA 12 - EMA 26), Signal line (9-day EMA of MACD), Histogram

Also provides interactive Plotly chart generators for technical visualizations.
"""

import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculates Simple Moving Average (SMA)."""
    if series.empty or window <= 0:
        return pd.Series(dtype=float)
    return series.rolling(window=window, min_periods=1).mean()


def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    if series.empty or span <= 0:
        return pd.Series(dtype=float)
    return series.ewm(span=span, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates Relative Strength Index (RSI) using Wilder's smoothing.
    """
    if series.empty or len(series) < 2 or period <= 0:
        return pd.Series(index=series.index, dtype=float)
    
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # Wilder's exponential smoothing (alpha = 1/period)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=1, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=1, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    # Where avg_loss was 0, RSI is 100; where avg_gain was 0, RSI is 0
    fill_vals = pd.Series(np.where(avg_gain == 0, 0.0, 100.0), index=rsi.index)
    rsi = rsi.fillna(fill_vals)
    # Neutral 50 for the first point where no price change exists
    rsi.iloc[0] = 50.0
    return rsi


def calculate_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Dict[str, pd.Series]:
    """
    Calculates MACD Line, Signal Line, and MACD Histogram.
    """
    if series.empty:
        empty = pd.Series(dtype=float)
        return {"macd": empty, "signal": empty, "histogram": empty}
    
    fast_ema = calculate_ema(series, fast_period)
    slow_ema = calculate_ema(series, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def compute_all_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches a price dataframe (requires 'close' or 'Close') with all target indicators:
    - SMA: 20, 50, 200
    - EMA: 12, 26, 50
    - RSI: 14
    - MACD: macd, signal, histogram
    """
    if df.empty:
        return df

    out = df.copy()
    close_col = "close" if "close" in out.columns else ("Close" if "Close" in out.columns else None)
    if not close_col:
        raise ValueError("DataFrame must contain 'close' or 'Close' column.")
    
    closes = pd.to_numeric(out[close_col], errors="coerce").ffill().bfill()

    # SMAs
    out["sma_20"] = calculate_sma(closes, 20).round(4)
    out["sma_50"] = calculate_sma(closes, 50).round(4)
    out["sma_200"] = calculate_sma(closes, 200).round(4)

    # EMAs
    out["ema_12"] = calculate_ema(closes, 12).round(4)
    out["ema_26"] = calculate_ema(closes, 26).round(4)
    out["ema_50"] = calculate_ema(closes, 50).round(4)

    # RSI
    out["rsi_14"] = calculate_rsi(closes, 14).round(4)

    # MACD
    macd_dict = calculate_macd(closes, 12, 26, 9)
    out["macd"] = macd_dict["macd"].round(4)
    out["macd_signal"] = macd_dict["signal"].round(4)
    out["macd_hist"] = macd_dict["histogram"].round(4)

    return out


def generate_interactive_stock_chart_plotly(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """
    Generates a Plotly multi-pane interactive chart:
    - Pane 1: Candlestick/Price with SMA(20, 50, 200) and EMA(12, 26, 50)
    - Pane 2: Volume
    - Pane 3: MACD & Signal line with histogram
    - Pane 4: RSI (14) with overbought (70) and oversold (30) levels
    Returns Plotly figure JSON dict.
    """
    enriched = compute_all_technical_indicators(df)
    date_col = "date" if "date" in enriched.columns else ("Date" if "Date" in enriched.columns else None)
    dates = enriched[date_col] if date_col else list(range(len(enriched)))

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            f"{symbol.upper()} Price & Moving Averages",
            "Trading Volume",
            "MACD (12, 26, 9)",
            "RSI (14)",
        ),
        row_heights=[0.50, 0.15, 0.18, 0.17],
    )

    close_col = "close" if "close" in enriched.columns else "Close"
    open_col = "open" if "open" in enriched.columns else "Open"
    high_col = "high" if "high" in enriched.columns else "High"
    low_col = "low" if "low" in enriched.columns else "Low"

    # Candlestick or line
    if open_col in enriched.columns and high_col in enriched.columns and low_col in enriched.columns:
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=enriched[open_col],
                high=enriched[high_col],
                low=enriched[low_col],
                close=enriched[close_col],
                name="Price",
            ),
            row=1,
            col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(x=dates, y=enriched[close_col], name="Close", line=dict(color="#3b82f6", width=2)),
            row=1,
            col=1,
        )

    # Overlays
    colors = {
        "sma_20": "#06b6d4",
        "sma_50": "#f59e0b",
        "sma_200": "#ef4444",
        "ema_12": "#10b981",
        "ema_26": "#8b5cf6",
        "ema_50": "#ec4899",
    }
    for col_name, color in colors.items():
        if col_name in enriched.columns:
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=enriched[col_name],
                    name=col_name.upper().replace("_", " "),
                    line=dict(color=color, width=1.2),
                ),
                row=1,
                col=1,
            )

    # Volume
    vol_col = "volume" if "volume" in enriched.columns else ("Volume" if "Volume" in enriched.columns else None)
    if vol_col and vol_col in enriched.columns:
        fig.add_trace(
            go.Bar(x=dates, y=enriched[vol_col], name="Volume", marker_color="#64748b", opacity=0.7),
            row=2,
            col=1,
        )

    # MACD
    fig.add_trace(
        go.Scatter(x=dates, y=enriched["macd"], name="MACD", line=dict(color="#3b82f6", width=1.5)),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=dates, y=enriched["macd_signal"], name="Signal", line=dict(color="#f59e0b", width=1.5)),
        row=3,
        col=1,
    )
    hist_colors = ["#10b981" if v >= 0 else "#ef4444" for v in enriched["macd_hist"].fillna(0)]
    fig.add_trace(
        go.Bar(x=dates, y=enriched["macd_hist"], name="Histogram", marker_color=hist_colors),
        row=3,
        col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=dates, y=enriched["rsi_14"], name="RSI (14)", line=dict(color="#8b5cf6", width=1.5)),
        row=4,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=4, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=4, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#060912",
        font=dict(color="#94a3b8"),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_rangeslider_visible=False,
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
