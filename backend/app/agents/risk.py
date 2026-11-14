"""Risk agent: volatility, drawdown, value-at-risk and beta from the price window, with
market-wide volatility (VIX / India VIX) as context. The score is a risk *tilt*: calm
stocks add a little, volatile ones subtract."""
import numpy as np
import pandas as pd

from ..data.macro import VolIndex
from ..data.prices import PriceData
from .base import AgentResult, clip, unavailable

NAME = "Risk"

# (annualised volatility upper bound, level, score)
_LEVELS = [(0.20, "Low", 0.15), (0.30, "Moderate", 0.0), (0.45, "High", -0.25), (9.99, "Very high", -0.5)]


def analyze(prices: PriceData, days: int, benchmark: PriceData | None, vol_index: VolIndex | None,
            notes: list[str] | None = None) -> AgentResult:
    close = prices.frame["close"]
    window = close[close.index >= close.index[-1] - pd.Timedelta(days=days)]
    returns = window.pct_change().dropna()
    if len(returns) < 15:
        return unavailable(NAME, f"Only {len(returns)} daily returns in the window; at least 15 are needed.")

    vol = float(returns.std() * np.sqrt(252))
    drawdown = float((window / window.cummax() - 1).min())
    var95 = float(-returns.quantile(0.05))
    level, base = next((lvl, s) for bound, lvl, s in _LEVELS if vol < bound)
    score = base + (-0.1 if drawdown < -0.30 else 0.0)

    points = [
        f"Annualised volatility: {vol * 100:.1f}% ({level.lower()} risk).",
        f"Worst peak-to-trough fall in the window: {drawdown * 100:.1f}%.",
        f"1-day 95% value-at-risk: on 1 in 20 days the stock has lost {var95 * 100:.1f}% or more.",
    ]
    metrics = {"annual_volatility": vol, "max_drawdown": drawdown, "var95_1d": var95, "level": level}
    sources = [f"{prices.source}, {prices.symbol}"]
    warnings = list(notes or [])

    if benchmark is not None:
        joined = pd.concat([window.pct_change(), benchmark.frame["close"].pct_change()], axis=1, join="inner").dropna()
        joined.columns = ["stock", "market"]
        if len(joined) >= 30 and joined["market"].var() > 0:
            beta = float(joined["stock"].cov(joined["market"]) / joined["market"].var())
            metrics["beta"] = beta
            how = "moves more than" if beta > 1.1 else "moves less than" if beta < 0.9 else "moves roughly in line with"
            points.append(f"Beta vs {benchmark.symbol}: {beta:.2f}; the stock {how} the market.")
            sources.append(f"Benchmark: {benchmark.symbol}")
        else:
            warnings.append("Not enough overlapping days with the market index to compute beta.")

    if vol_index is not None:
        calm = "calm" if vol_index.percentile < 0.33 else "elevated" if vol_index.percentile > 0.66 else "typical"
        points.append(f"{vol_index.name} is {vol_index.latest:.1f} ({calm}; higher than {vol_index.percentile * 100:.0f}% "
                      f"of the past year), as of {vol_index.as_of}.")
        sources.append(f"{vol_index.name}: {vol_index.source}")
        metrics["vol_index"] = vol_index.latest
        if vol_index.percentile > 0.8:
            score -= 0.1

    if len(returns) < 60:
        warnings.append("The window is short, so the risk estimates are noisy. Use a longer period for steadier numbers.")

    return AgentResult(NAME, clip(score), f"{level} risk", points, sources, warnings, metrics)
