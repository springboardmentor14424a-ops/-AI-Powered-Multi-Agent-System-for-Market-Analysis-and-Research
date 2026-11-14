"""Combines the agents' scores into one rule-based report."""
from datetime import date

import pandas as pd

from ..data.prices import PriceData
from ..stocks import PERIOD_DAYS
from .base import AgentResult

STALE_DAYS = 10  # prices older than this (calendar days) trigger the stale-data banner

# Relative importance of each agent; renormalised over the agents that actually ran.
WEIGHTS = {"Technical": 0.30, "Sentiment": 0.25, "Fundamentals": 0.30, "Risk": 0.15}

DISCLAIMER = (
    "This report is generated automatically from historical data using fixed rules. It is for "
    "education and research only and is not financial advice."
)


def combine(results: list[AgentResult]) -> tuple[float | None, str]:
    """Weighted average of the available scores, plus a confidence label."""
    ran = [r for r in results if r.available]
    if not ran:
        return None, "None"
    total = sum(WEIGHTS[r.name] for r in ran)
    overall = sum(WEIGHTS[r.name] * r.score for r in ran) / total
    spread = max(r.score for r in ran) - min(r.score for r in ran)
    if len(ran) >= 4 and spread < 0.6:
        confidence = "High"
    elif len(ran) < 3 or spread > 1.0:
        confidence = "Low"
    else:
        confidence = "Medium"
    return overall, confidence


def verdict(overall: float) -> str:
    if overall > 0.2:
        return "Leaning positive"
    if overall < -0.2:
        return "Leaning negative"
    return "Mixed / neutral"


def build_report(task, prices: PriceData, results: list[AgentResult]) -> str:
    days = PERIOD_DAYS.get(task.analysis_period, "?")
    overall, confidence = combine(results)
    ran = [r for r in results if r.available]

    # A view built on old prices must not read like a current one.
    age = (pd.Timestamp.today().normalize() - prices.last_date).days
    stale = age > STALE_DAYS
    if stale:
        confidence = "Low"

    lines = [
        f"RESEARCH REPORT: {task.company_name} ({task.ticker})",
        f"Market: {task.market}   |   Analysis period: {task.analysis_period}   |   Generated: {date.today():%Y-%m-%d}",
        f"Data window: ~{days} days of daily prices for {prices.symbol} (latest price date {prices.last_date:%Y-%m-%d})",
    ]
    if stale:
        lines.append(
            f"*** STALE DATA: the newest price is from {prices.last_date:%Y-%m-%d} ({age:,} days ago). This report describes "
            "that date, not today. Connect to the internet for live prices. ***"
        )
    lines += [
        "",
        f"OVERALL VIEW: {verdict(overall)}  (score {overall:+.2f} on a -1 to +1 scale, confidence: {confidence})",
        f"Based on {len(ran)} of {len(results)} agents. Weights: "
        + ", ".join(f"{k} {int(v * 100)}%" for k, v in WEIGHTS.items()) + ".",
    ]
    if ran:
        best = max(ran, key=lambda r: r.score)
        worst = min(ran, key=lambda r: r.score)
        if best is not worst:
            lines.append(f"Strongest signal: {best.name} ({best.score:+.2f}). Weakest: {worst.name} ({worst.score:+.2f}).")

    for r in results:
        lines += ["", f"{r.name.upper()} AGENT: {r.label}" + (f" ({r.score:+.2f})" if r.available else "")]
        lines += [f"  - {p}" for p in r.points]
        lines += [f"  ! {w}" for w in r.warnings]

    sources = []
    for r in results:
        for s in r.sources:
            if s not in sources:
                sources.append(s)
    lines += ["", "DATA SOURCES"] + [f"  - {s}" for s in sources]
    lines += ["", "NOTE", f"  {DISCLAIMER}"]
    return "\n".join(lines)
