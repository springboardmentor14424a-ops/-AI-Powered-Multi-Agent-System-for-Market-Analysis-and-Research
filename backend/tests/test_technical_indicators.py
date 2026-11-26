"""
Unit tests for Technical Indicators:
- SMA (20, 50, 200)
- EMA (12, 26, 50)
- RSI (14)
- MACD (12, 26, 9)
- Chart JSON generation and edge cases
"""

import pytest
import pandas as pd
import numpy as np
from app.services.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    compute_all_technical_indicators,
    generate_interactive_stock_chart_plotly,
)


def test_sma_calculation_exact():
    series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    # Window 3 with min_periods=1
    sma3 = calculate_sma(series, window=3)
    assert sma3.iloc[0] == 10.0
    assert sma3.iloc[1] == (10.0 + 20.0) / 2.0  # 15.0
    assert sma3.iloc[2] == (10.0 + 20.0 + 30.0) / 3.0  # 20.0
    assert sma3.iloc[3] == (20.0 + 30.0 + 40.0) / 3.0  # 30.0
    assert sma3.iloc[4] == (30.0 + 40.0 + 50.0) / 3.0  # 40.0


def test_sma_empty_and_invalid():
    empty = pd.Series(dtype=float)
    assert calculate_sma(empty, 20).empty
    assert calculate_sma(pd.Series([1.0, 2.0]), window=0).empty
    assert calculate_sma(pd.Series([1.0, 2.0]), window=-5).empty


def test_ema_calculation():
    series = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])
    ema = calculate_ema(series, span=3)
    assert len(ema) == len(series)
    assert ema.iloc[0] == 10.0
    # Formula for adjust=False: ema_t = alpha * x_t + (1 - alpha) * ema_{t-1}, alpha = 2/(span+1) = 0.5
    # ema_1 = 0.5 * 11.0 + 0.5 * 10.0 = 10.5
    assert pytest.approx(ema.iloc[1], 0.01) == 10.5
    # ema_2 = 0.5 * 12.0 + 0.5 * 10.5 = 11.25
    assert pytest.approx(ema.iloc[2], 0.01) == 11.25


def test_rsi_constant_upward():
    # Continual gains should yield RSI of 100
    prices = pd.Series([float(i) for i in range(1, 30)])
    rsi = calculate_rsi(prices, period=14)
    # The last values must be 100.0
    assert pytest.approx(rsi.iloc[-1], 0.01) == 100.0


def test_rsi_constant_downward():
    # Continual losses should yield RSI of 0
    prices = pd.Series([float(30 - i) for i in range(30)])
    rsi = calculate_rsi(prices, period=14)
    assert pytest.approx(rsi.iloc[-1], 0.01) == 0.0


def test_rsi_bounded_and_edge_cases():
    # Oscillating series
    np.random.seed(42)
    series = pd.Series(100.0 + np.cumsum(np.random.randn(100)))
    rsi = calculate_rsi(series, period=14)
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0.0).all()
    assert (valid_rsi <= 100.0).all()

    # Empty and very short series
    assert calculate_rsi(pd.Series(dtype=float)).empty
    assert calculate_rsi(pd.Series([50.0])).iloc[0] != calculate_rsi(pd.Series([50.0])).iloc[0] or pd.isna(calculate_rsi(pd.Series([50.0])).iloc[0])


def test_macd_calculation():
    series = pd.Series([100.0 + i * 0.5 for i in range(50)])
    result = calculate_macd(series, fast_period=12, slow_period=26, signal_period=9)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result
    
    # Check relationship histogram = macd - signal
    diff = result["macd"] - result["signal"]
    pd.testing.assert_series_equal(diff, result["histogram"], check_names=False)


def test_compute_all_technical_indicators():
    n = 250
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "open": np.linspace(100, 150, n),
        "high": np.linspace(105, 155, n),
        "low": np.linspace(95, 145, n),
        "close": np.linspace(102, 152, n),
        "volume": np.random.randint(100000, 500000, n),
    })

    enriched = compute_all_technical_indicators(df)
    
    expected_cols = [
        "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26", "ema_50",
        "rsi_14", "macd", "macd_signal", "macd_hist"
    ]
    for col in expected_cols:
        assert col in enriched.columns, f"Missing column: {col}"
        # Ensure values are numeric and not all NaN
        assert pd.notnull(enriched[col].iloc[-1])


def test_generate_interactive_stock_chart_plotly():
    n = 60
    df = pd.DataFrame({
        "date": [f"2024-01-{i+1:02d}" for i in range(n)],
        "open": np.linspace(100, 120, n),
        "high": np.linspace(102, 122, n),
        "low": np.linspace(98, 118, n),
        "close": np.linspace(101, 121, n),
        "volume": [100000] * n,
    })

    chart = generate_interactive_stock_chart_plotly(df, "TEST")
    assert isinstance(chart, dict)
    assert "data" in chart
    assert "layout" in chart
    assert len(chart["data"]) > 0
