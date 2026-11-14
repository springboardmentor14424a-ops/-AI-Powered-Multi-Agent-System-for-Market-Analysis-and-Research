"""Fundamentals agent: growth, profitability, leverage and valuation from whichever
of these figures the data source provides."""
from ..data.fundamentals import Fundamentals
from .base import AgentResult, clip, pct, stance, unavailable

NAME = "Fundamentals"


def _money(x: float) -> str:
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if abs(x) >= size:
            return f"{x / size:,.2f}{unit}"
    return f"{x:,.0f}"


def analyze(f: Fundamentals) -> AgentResult:
    m = f.metrics
    score, points, scored = 0.0, [], 0

    g = m.get("revenue_growth")
    if g is not None:
        scored += 1
        score += 0.3 if g > 0.10 else 0.1 if g > 0 else -0.3
        points.append(f"Revenue growth: {pct(g)} ({'strong' if g > 0.10 else 'modest' if g > 0 else 'shrinking'}).")

    nm = m.get("net_margin")
    if nm is not None:
        scored += 1
        score += 0.25 if nm > 0.15 else 0.05 if nm > 0.05 else -0.1 if nm >= 0 else -0.4
        points.append(f"Net profit margin: {nm * 100:.1f}% ({'high' if nm > 0.15 else 'healthy' if nm > 0.05 else 'thin' if nm >= 0 else 'loss-making'}).")

    roe = m.get("roe")
    if roe is not None:
        scored += 1
        score += 0.25 if roe > 0.15 else 0.05 if roe > 0.08 else -0.15
        points.append(f"Return on equity: {roe * 100:.1f}%.")

    la = m.get("liabilities_to_assets")
    if la is not None:
        scored += 1
        score += 0.1 if la < 0.6 else -0.1 if la < 0.8 else -0.25
        points.append(f"Liabilities are {la * 100:.0f}% of assets ({'conservative' if la < 0.6 else 'moderate' if la < 0.8 else 'heavy'} leverage).")

    de = m.get("debt_to_equity")
    if de is not None:
        scored += 1
        score += 0.1 if de < 0.5 else 0.0 if de < 1.5 else -0.2
        points.append(f"Debt-to-equity: {de:.2f}x.")

    pe = m.get("trailing_pe")
    if pe is not None and pe > 0:
        scored += 1
        score += 0.1 if pe < 15 else 0.0 if pe < 30 else -0.15
        points.append(f"Trailing P/E: {pe:.1f} ({'inexpensive' if pe < 15 else 'fair' if pe < 30 else 'expensive'} relative to earnings).")
    elif pe is not None:
        points.append("Trailing P/E is not meaningful (negative earnings).")

    pb = m.get("price_to_book")
    if pb is not None:
        points.append(f"Price-to-book: {pb:.1f}.")
    if "revenue" in m:
        points.append(f"Latest annual revenue: {_money(m['revenue'])}" + (f", net income: {_money(m['net_income'])}." if "net_income" in m else "."))
    if "market_cap" in m:
        points.append(f"Market capitalisation: {_money(m['market_cap'])}.")

    if scored == 0:
        return unavailable(NAME, "The data source returned no scoreable fundamentals.")

    score = clip(score)
    warnings = list(f.notes)
    if f.as_of:
        warnings.append(f"Based on the fiscal year ending {f.as_of}.")
    return AgentResult(NAME, score, stance(score), points, [f.source], warnings, dict(m))
