import pytest

import helpers
from app.agents import AnalysisError, fundamentals, risk, run_analysis, sentiment, technical
from app.agents.report import WEIGHTS, combine, verdict
from app.agents.base import AgentResult
from app.data import DataUnavailable


class Task:
    company_name = "Apple Inc."
    ticker = "AAPL"
    market = "NASDAQ"
    analysis_period = "1 year"


# ---------------------------------------------------------------- technical

def test_technical_uptrend_is_bullish_and_downtrend_bearish():
    up = technical.analyze(helpers.trend_prices(up=True), 365)
    down = technical.analyze(helpers.trend_prices(up=False), 365)
    assert up.score > 0.5 and up.label == "Bullish"
    # A relentless fall still scores Bearish, but less extremely than a rise scores
    # Bullish: the oversold-RSI and MACD-histogram rules deliberately push back.
    assert down.score < -0.25 and down.label == "Bearish"
    assert up.score - down.score > 0.8
    assert any("50-day average" in p for p in up.points)
    assert -1 <= up.score <= 1 and -1 <= down.score <= 1


def test_technical_needs_enough_history():
    r = technical.analyze(helpers.make_prices(n=30), 30)
    assert not r.available and "at least 60" in r.warnings[0]


def test_technical_warns_about_stale_data():
    import pandas as pd

    p = helpers.make_prices(n=300)
    p.frame.index = p.frame.index - pd.Timedelta(days=400)
    assert any("ends" in w for w in technical.analyze(p, 90).warnings)


# --------------------------------------------------------------------- risk

def test_risk_matches_known_volatility():
    # daily sigma 0.02 -> annualised ~ 0.02 * sqrt(252) = 31.7%
    r = risk.analyze(helpers.make_prices(sigma=0.02, drift=0, n=1200), 1000, None, None)
    assert r.metrics["annual_volatility"] == pytest.approx(0.317, abs=0.04)
    assert r.label == "High risk"
    assert r.metrics["max_drawdown"] < 0 and r.metrics["var95_1d"] > 0


def test_risk_calm_stock_scores_better_than_wild_stock():
    calm = risk.analyze(helpers.make_prices(sigma=0.007, n=600), 365, None, None)
    wild = risk.analyze(helpers.make_prices(sigma=0.04, n=600), 365, None, None)
    assert calm.label == "Low risk" and wild.label == "Very high risk"
    assert calm.score > wild.score


def test_risk_beta_of_the_market_against_itself_is_one():
    p = helpers.make_prices(seed=5, n=600)
    r = risk.analyze(p, 365, p, helpers.make_vol_index())
    assert r.metrics["beta"] == pytest.approx(1.0, abs=1e-6)
    assert any("VIX" in s for s in r.sources)


def test_risk_short_window_is_flagged_noisy():
    r = risk.analyze(helpers.make_prices(n=600), 30, None, None)
    assert r.available and any("noisy" in w for w in r.warnings)


# ---------------------------------------------------------------- sentiment

def test_sentiment_keyword_fallback_separates_good_and_bad_news():
    good = sentiment.analyze(helpers.make_news(helpers.POSITIVE), 90)
    bad = sentiment.analyze(helpers.make_news(helpers.NEGATIVE), 90)
    assert good.score > 0.3 and good.label == "Positive"
    assert bad.score < -0.3 and bad.label == "Negative"
    assert any("keyword" in w for w in good.warnings)  # honest about the fallback


def test_sentiment_needs_a_few_headlines_and_flags_old_news():
    assert not sentiment.analyze(helpers.make_news(helpers.POSITIVE[:2]), 90).available
    import pandas as pd

    old = helpers.make_news(helpers.POSITIVE, end=pd.Timestamp.today().normalize() - pd.Timedelta(days=400))
    r = sentiment.analyze(old, 90)
    assert r.available and any("days ago" in w for w in r.warnings)


# ------------------------------------------------------------- fundamentals

def test_fundamentals_strong_vs_weak():
    strong = fundamentals.analyze(helpers.make_fundamentals())
    weak = fundamentals.analyze(
        helpers.make_fundamentals(revenue_growth=-0.1, net_margin=-0.05, roe=0.01, liabilities_to_assets=0.9)
    )
    assert strong.score > 0.5 and strong.label == "Bullish"
    assert weak.score < -0.5 and weak.label == "Bearish"


def test_fundamentals_with_no_scoreable_metrics_is_unavailable():
    from app.data.fundamentals import Fundamentals

    assert not fundamentals.analyze(Fundamentals({"market_cap": 1e9}, "x")).available


# ---------------------------------------------------------------- synthesis

def _r(name, score):
    return AgentResult(name, score, "x")


def test_combine_weights_and_renormalises_over_available_agents():
    overall, conf = combine([_r("Technical", 1.0), _r("Sentiment", 1.0), _r("Fundamentals", -1.0), _r("Risk", 0.0)])
    expected = (0.30 * 1 + 0.25 * 1 + 0.30 * -1 + 0.15 * 0) / sum(WEIGHTS.values())
    assert overall == pytest.approx(expected)
    assert conf == "Low"  # agents disagree strongly

    overall, conf = combine([_r("Technical", 0.5), _r("Sentiment", None), _r("Fundamentals", 0.5), _r("Risk", None)])
    assert overall == pytest.approx(0.5) and conf == "Low"  # only 2 of 4 ran

    assert combine([_r("Technical", None)]) == (None, "None")
    assert combine([_r(n, 0.4) for n in WEIGHTS])[1] == "High"


def test_verdict_thresholds():
    assert verdict(0.3) == "Leaning positive" and verdict(-0.3) == "Leaning negative" and verdict(0.0) == "Mixed / neutral"


# ------------------------------------------------------------- orchestrator

def test_full_report_has_every_section():
    report = run_analysis(Task())
    for text in ["RESEARCH REPORT: Apple Inc. (AAPL)", "OVERALL VIEW", "TECHNICAL AGENT", "SENTIMENT AGENT",
                 "FUNDAMENTALS AGENT", "RISK AGENT", "DATA SOURCES", "not financial advice", "~365 days"]:
        assert text in report, text


def test_one_failing_agent_does_not_fail_the_report(monkeypatch):
    def no_news(*a):
        raise DataUnavailable("No news available.")

    monkeypatch.setattr("app.data.news.get_news", no_news)
    report = run_analysis(Task())
    assert "SENTIMENT AGENT: Unavailable" in report and "No news available." in report
    assert "TECHNICAL AGENT: " in report and "Based on 3 of 4 agents" in report


def test_a_crashing_agent_is_contained(monkeypatch):
    def boom(*a):
        raise RuntimeError("secret internals")

    monkeypatch.setattr("app.data.fundamentals.get_fundamentals", boom)
    report = run_analysis(Task())
    assert "FUNDAMENTALS AGENT: Unavailable" in report
    assert "secret internals" not in report  # details go to the log, not the report


def test_missing_benchmark_and_vix_only_weaken_the_risk_agent(monkeypatch):
    def gone(*a):
        raise DataUnavailable("offline")

    monkeypatch.setattr("app.data.prices.get_benchmark", gone)
    monkeypatch.setattr("app.data.macro.get_volatility_index", gone)
    report = run_analysis(Task())
    assert "RISK AGENT: " in report and "beta was skipped" in report


def test_old_prices_get_a_banner_and_low_confidence(monkeypatch):
    import pandas as pd

    def old_prices(market, ticker, days):
        p = helpers.make_prices()
        p.frame.index = p.frame.index - pd.Timedelta(days=1000)
        return p

    monkeypatch.setattr("app.data.prices.get_prices", old_prices)
    report = run_analysis(Task())
    assert "*** STALE DATA" in report and "confidence: Low" in report


def test_fresh_prices_have_no_banner():
    assert "STALE DATA" not in run_analysis(Task())


def test_network_errors_are_summarised_not_dumped_into_the_report(monkeypatch):
    import yfinance

    def blocked(symbol):
        raise RuntimeError("Failed to perform, curl: (7) CONNECT tunnel failed, response 403. See https://curl.se/libcurl")

    monkeypatch.setattr(yfinance, "Ticker", blocked)
    from app.data import prices

    with pytest.raises(DataUnavailable) as e:
        prices.fetch_live("AAPL", 400)
    assert "curl" not in str(e.value) and "AAPL" in str(e.value)


def test_no_price_data_fails_with_a_clear_message(monkeypatch):
    def gone(*a):
        raise DataUnavailable("offline")

    monkeypatch.setattr("app.data.prices.get_prices", gone)
    with pytest.raises(AnalysisError) as e:
        run_analysis(Task())
    assert "No price data could be retrieved for AAPL" in str(e.value)
