"""Multi-agent analysis: four specialist agents look at one stock, then their scores are
combined into a single report. An agent that can't get its data is reported as
"Unavailable" instead of failing the whole analysis; only missing price data (the
foundation for everything else) fails the task."""
import logging

from ..data import DataUnavailable
from ..data import fundamentals as fundamentals_data
from ..data import macro as macro_data
from ..data import news as news_data
from ..data import prices as price_data
from ..stocks import PERIOD_DAYS
from . import fundamentals, risk, sentiment, technical
from .base import AgentResult, unavailable
from .report import build_report

log = logging.getLogger(__name__)


class AnalysisError(Exception):
    """The analysis can't be produced. The message is safe to show to the user."""


def _safe(name: str, fn) -> AgentResult:
    """Run one agent so a failure in it never takes down the others."""
    try:
        return fn()
    except DataUnavailable as e:
        return unavailable(name, str(e))
    except Exception:
        log.exception("%s agent crashed", name)
        return unavailable(name, "This agent hit an unexpected error. Details are in the server log.")


def run_analysis(task) -> str:
    days = PERIOD_DAYS[task.analysis_period]

    try:
        prices = price_data.get_prices(task.market, task.ticker, days)
    except DataUnavailable as e:
        log.warning("No price data for %s %s: %s", task.market, task.ticker, e)
        raise AnalysisError(
            f"No price data could be retrieved for {task.ticker} on {task.market}. Check the ticker and "
            "your internet connection (for NSE stocks you can also download the offline dataset; see the README)."
        ) from e

    def run_risk() -> AgentResult:
        notes = []
        try:
            benchmark = price_data.get_benchmark(task.market, days)
        except DataUnavailable as e:
            benchmark = None
            notes.append(f"Market index unavailable, so beta was skipped ({e}).")
        try:
            vol_index = macro_data.get_volatility_index(task.market)
        except DataUnavailable as e:
            vol_index = None
            notes.append(f"Volatility index unavailable ({e}).")
        return risk.analyze(prices, days, benchmark, vol_index, notes)

    results = [
        _safe("Technical", lambda: technical.analyze(prices, days)),
        _safe("Sentiment", lambda: sentiment.analyze(news_data.get_news(task.market, task.ticker, task.company_name), days)),
        _safe("Fundamentals", lambda: fundamentals.analyze(fundamentals_data.get_fundamentals(task.market, task.ticker))),
        _safe("Risk", run_risk),
    ]
    return build_report(task, prices, results)
