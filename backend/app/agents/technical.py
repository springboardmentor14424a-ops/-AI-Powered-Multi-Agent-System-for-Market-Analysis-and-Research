"""Technical agent: trend, momentum and price-position rules on daily closes.
Every rule adds or subtracts a fixed amount, so the score is easy to explain."""
import math

import pandas as pd

from ..data.prices import PriceData
from .base import AgentResult, clip, pct, stance, unavailable

NAME = "Technical"


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / down)


def analyze(prices: PriceData, days: int) -> AgentResult:
    close = prices.frame["close"]
    if len(close) < 60:
        return unavailable(NAME, f"Only {len(close)} days of prices; at least 60 are needed.")

    last = float(close.iloc[-1])
    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else math.nan
    rsi14 = float(rsi(close).iloc[-1])
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_hist = float((macd - macd.ewm(span=9, adjust=False).mean()).iloc[-1])
    window = close[close.index >= close.index[-1] - pd.Timedelta(days=days)]
    period_return = last / float(window.iloc[0]) - 1
    year = close.iloc[-252:]
    hi, lo = float(year.max()), float(year.min())
    range_pos = (last - lo) / (hi - lo) if hi > lo else 0.5

    score, points = 0.0, []

    above50 = last > sma50
    score += 0.25 if above50 else -0.25
    points.append(f"Price {last:,.2f} is {'above' if above50 else 'below'} its 50-day average ({sma50:,.2f}): "
                  f"{'short-term uptrend' if above50 else 'short-term downtrend'}.")

    if not math.isnan(sma200):
        golden = sma50 > sma200
        score += 0.25 if golden else -0.25
        points.append(f"50-day average is {'above' if golden else 'below'} the 200-day ({sma200:,.2f}): "
                      f"{'long-term uptrend' if golden else 'long-term downtrend'}.")

    score += 0.2 if macd_hist > 0 else -0.2
    points.append(f"MACD histogram is {'positive' if macd_hist > 0 else 'negative'}: momentum is "
                  f"{'building' if macd_hist > 0 else 'fading'}.")

    if rsi14 > 70:
        score -= 0.15
        points.append(f"RSI is {rsi14:.0f} (above 70): overbought, so a pullback is more likely.")
    elif rsi14 < 30:
        score += 0.15
        points.append(f"RSI is {rsi14:.0f} (below 30): oversold, so a rebound is more likely.")
    else:
        points.append(f"RSI is {rsi14:.0f}: neither overbought nor oversold.")

    score += 0.15 if period_return > 0 else -0.15
    points.append(f"Return over the analysis window: {pct(period_return)}.")
    points.append(f"Trading at {range_pos * 100:.0f}% of its 52-week range ({lo:,.2f} to {hi:,.2f}).")

    score = clip(score)
    warnings = []
    age = (pd.Timestamp.today().normalize() - prices.last_date).days
    if age > 10:
        warnings.append(f"Price data ends {prices.last_date:%Y-%m-%d} ({age} days ago), so this reflects that date, not today.")

    return AgentResult(
        NAME, score, stance(score), points, [f"{prices.source}, {prices.symbol}"], warnings,
        {"last_close": last, "sma20": sma20, "sma50": sma50, "sma200": None if math.isnan(sma200) else sma200,
         "rsi14": rsi14, "macd_hist": macd_hist, "period_return": period_return, "range_position": range_pos},
    )
