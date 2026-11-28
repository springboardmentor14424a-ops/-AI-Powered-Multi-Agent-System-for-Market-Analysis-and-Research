from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

DISCLAIMER = (
    "Technical indicators describe historical market conditions "
    "and should not be treated as guaranteed predictions."
)


def calculate_sma(close_prices, window):
    """Simple Moving Average: average of the last `window` closing prices."""
    return close_prices.rolling(window=window).mean()


def calculate_ema(close_prices, window):
    """Exponential Moving Average: like SMA, but recent prices count more."""
    return close_prices.ewm(span=window, adjust=False).mean()


def calculate_rsi(close_prices, window=14):
    """Relative Strength Index (0 to 100): how strong recent gains are
    compared with recent losses. Uses the standard Wilder method."""
    change = close_prices.diff()
    gains = change.clip(lower=0)
    losses = -change.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    """MACD: momentum indicator built from two EMAs.
    Returns a table with the MACD line, the signal line and the histogram."""
    ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
    ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    })


def calculate_price_trend(close_prices):
    """Historical price trend: how much the price changed over 1 month,
    3 months and the whole period, plus an Upward / Downward / Mixed label
    based on the latest price and the 20-day and 50-day SMA."""
    if len(close_prices) < 64:
        return {"trend": "Not enough data", "reason": "Need at least 64 trading days"}

    latest = float(close_prices.iloc[-1])
    sma20 = float(calculate_sma(close_prices, 20).iloc[-1])
    sma50 = float(calculate_sma(close_prices, 50).iloc[-1])

    change_1m = (latest / float(close_prices.iloc[-22]) - 1) * 100
    change_3m = (latest / float(close_prices.iloc[-64]) - 1) * 100
    change_period = (latest / float(close_prices.iloc[0]) - 1) * 100

    if latest > sma20 > sma50:
        trend = "Upward trend"
    elif latest < sma20 < sma50:
        trend = "Downward trend"
    else:
        trend = "Mixed / sideways"

    return {
        "latest_close": round(latest, 2),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "change_1m_pct": round(change_1m, 2),
        "change_3m_pct": round(change_3m, 2),
        "change_period_pct": round(change_period, 2),
        "trend": trend,
    }


def calculate_volatility(close_prices, window=30):
    """Historical volatility: how much the daily % change varies.
    Returns the annualised volatility (in %) over the last `window` days
    and over the whole period, with a simple Low / Moderate / High label."""
    daily_returns = close_prices.pct_change().dropna()
    if len(daily_returns) < window:
        return {"volatility_label": "Not enough data"}

    recent = float(daily_returns.iloc[-window:].std() * (252 ** 0.5) * 100)
    overall = float(daily_returns.std() * (252 ** 0.5) * 100)

    if recent < 20:
        label = "Low"
    elif recent < 35:
        label = "Moderate"
    else:
        label = "High"

    return {
        "volatility_30d_pct": round(recent, 2),
        "volatility_period_pct": round(overall, 2),
        "volatility_label": label,
    }


def evaluate_conditions(latest, sma20, sma50, rsi, macd_value, signal_value):
    """Predefined technical conditions: fixed rules that turn the numbers
    into plain-English signals, plus an overall summary."""
    conditions = []

    # Rule 1: price vs 20-day SMA
    if latest > sma20:
        conditions.append({
            "name": "Price vs 20-day SMA", "signal": "bullish",
            "explanation": "Price is above its 20-day average, so recent momentum is positive.",
        })
    else:
        conditions.append({
            "name": "Price vs 20-day SMA", "signal": "bearish",
            "explanation": "Price is below its 20-day average, so recent momentum is weak.",
        })

    # Rule 2: 20-day SMA vs 50-day SMA
    if sma20 > sma50:
        conditions.append({
            "name": "20-day SMA vs 50-day SMA", "signal": "bullish",
            "explanation": "The short-term average is above the longer-term average, which suggests an uptrend.",
        })
    else:
        conditions.append({
            "name": "20-day SMA vs 50-day SMA", "signal": "bearish",
            "explanation": "The short-term average is below the longer-term average, which suggests a downtrend.",
        })

    # Rule 3: MACD line vs signal line
    if macd_value > signal_value:
        conditions.append({
            "name": "MACD vs Signal line", "signal": "bullish",
            "explanation": "The MACD line is above its signal line, so momentum is building up.",
        })
    else:
        conditions.append({
            "name": "MACD vs Signal line", "signal": "bearish",
            "explanation": "The MACD line is below its signal line, so momentum is fading.",
        })

    # Rule 4: RSI zones (information only, not counted in the overall score)
    if rsi > 70:
        rsi_signal = "overbought"
        rsi_text = "RSI is above 70: the price has risen very fast and may be stretched."
    elif rsi < 30:
        rsi_signal = "oversold"
        rsi_text = "RSI is below 30: the price has fallen very fast and may be stretched."
    else:
        rsi_signal = "neutral"
        rsi_text = "RSI is between 30 and 70: no extreme condition."
    conditions.append({"name": "RSI zone", "signal": rsi_signal, "explanation": rsi_text})

    bullish = sum(1 for c in conditions[:3] if c["signal"] == "bullish")
    bearish = sum(1 for c in conditions[:3] if c["signal"] == "bearish")

    if bullish >= 2 and bearish == 0:
        overall = "Upward (bullish) signals"
    elif bearish >= 2 and bullish == 0:
        overall = "Downward (bearish) signals"
    else:
        overall = "Mixed signals"

    return {
        "conditions": conditions,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "overall_signal": overall,
    }


def build_chart_data(close_prices):
    """Day-by-day table for the charts: one row per trading day with the
    closing price and every indicator. Days where an indicator cannot be
    calculated yet (for example SMA 50 in the first 49 days) are left empty."""
    macd = calculate_macd(close_prices)
    table = pd.DataFrame({
        "close": close_prices,
        "sma20": calculate_sma(close_prices, 20),
        "sma50": calculate_sma(close_prices, 50),
        "ema20": calculate_ema(close_prices, 20),
        "rsi14": calculate_rsi(close_prices, 14),
        "macd": macd["macd"],
        "signal": macd["signal"],
        "histogram": macd["histogram"],
    }).round(2)
    table.index = table.index.strftime("%Y-%m-%d")
    table = table.astype(object).where(table.notna(), None)

    rows = []
    for date, row in table.iterrows():
        item = {"date": date}
        item.update(row.to_dict())
        rows.append(item)
    return rows


def run_technical_agent(ticker, period="6mo"):
    """The Technical Analysis Agent: gets prices, calculates every indicator
    and returns one result with the data source and timestamp."""
    data = yf.Ticker(ticker).history(period=period)
    if data.empty:
        return {"ticker": ticker, "status": "failed", "error": "No price data found"}

    close = data["Close"]
    if len(close) < 64:
        return {"ticker": ticker, "status": "failed",
                "error": "Not enough price history (need at least 64 trading days)"}

    macd = calculate_macd(close)
    latest = float(close.iloc[-1])
    sma20 = float(calculate_sma(close, 20).iloc[-1])
    sma50 = float(calculate_sma(close, 50).iloc[-1])
    ema20 = float(calculate_ema(close, 20).iloc[-1])
    rsi = float(calculate_rsi(close, 14).iloc[-1])
    macd_value = float(macd["macd"].iloc[-1])
    signal_value = float(macd["signal"].iloc[-1])
    histogram = float(macd["histogram"].iloc[-1])

    return {
        "ticker": ticker,
        "status": "ok",
        "period": period,
        "source": "Yahoo Finance (yfinance)",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "indicators": {
            "latest_close": round(latest, 2),
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "ema20": round(ema20, 2),
            "rsi14": round(rsi, 2),
            "macd": round(macd_value, 2),
            "macd_signal": round(signal_value, 2),
            "macd_histogram": round(histogram, 2),
        },
        "price_trend": calculate_price_trend(close),
        "volatility": calculate_volatility(close),
        "technical_conditions": evaluate_conditions(
            latest, sma20, sma50, rsi, macd_value, signal_value
        ),
        "chart_data": build_chart_data(close),
        "disclaimer": DISCLAIMER,
    }
