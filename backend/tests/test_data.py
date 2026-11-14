"""Loader tests: real loaders reading files written in each dataset's format."""
import json

import numpy as np
import pandas as pd
import pytest

import helpers
from app.config import settings
from app.data import DataUnavailable, fundamentals, macro, news, prices, sentiment_model


# ------------------------------------------------------------------- prices

def _nifty_csv(path, rows=500):
    """Mimics Kaggle 'NIFTY-50 Stock Market Data' (rohanrao): one CSV per company."""
    idx = pd.bdate_range("2019-01-01", periods=rows)
    close = 1000 + np.arange(rows, dtype=float)
    pd.DataFrame({
        "Date": idx.strftime("%Y-%m-%d"), "Symbol": "RELIANCE", "Series": "EQ", "Prev Close": close - 1,
        "Open": close, "High": close + 5, "Low": close - 5, "Last": close, "Close": close, "VWAP": close,
        "Volume": 1_000_000, "Turnover": 1e12, "Trades": 1000, "Deliverable Volume": 500_000, "%Deliverble": 0.5,
    }).to_csv(path, index=False)


def test_clean_handles_yfinance_shape():
    idx = pd.date_range("2025-01-01", periods=5, freq="D", tz="America/New_York")
    raw = pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": 0.5, "Close": [1, 2, 3, 4, 5.0], "Volume": 10,
                        "Dividends": 0.0, "Stock Splits": 0.0}, index=idx)
    df = prices._clean(raw)
    assert list(df.columns) == prices.COLUMNS and df.index.tz is None
    assert df.index[0] == pd.Timestamp("2025-01-01")  # calendar date preserved


def test_offline_nifty_fallback_for_nse_only(monkeypatch):
    root = settings.DATA_DIR / "raw" / "nifty50"
    root.mkdir(parents=True)
    _nifty_csv(root / "RELIANCE.csv")

    def offline(symbol, need):
        raise DataUnavailable("no internet")

    monkeypatch.setattr(prices, "fetch_live", offline)
    p = helpers.REAL_GET_PRICES("NSE", "RELIANCE", 365)
    assert "Kaggle NIFTY-50" in p.source and p.symbol == "RELIANCE.NS"
    assert len(p.frame) > 100 and p.frame["close"].iloc[-1] > 1000

    with pytest.raises(DataUnavailable):  # same ticker on another market must not use it
        helpers.REAL_GET_PRICES("BSE", "500325", 365)
    with pytest.raises(DataUnavailable):
        helpers.REAL_GET_PRICES("NSE", "NOTINSET", 365)


def test_live_prices_are_cached(monkeypatch):
    calls = []

    def fake_live(symbol, need):
        calls.append(symbol)
        return helpers.make_prices(n=500).frame

    monkeypatch.setattr(prices, "fetch_live", fake_live)
    first = helpers.REAL_GET_PRICES("NASDAQ", "AAPL", 365)
    second = helpers.REAL_GET_PRICES("NASDAQ", "AAPL", 365)
    assert calls == ["AAPL"]  # second call served from the cache
    assert "yfinance" in first.source and "cached" in second.source
    assert len(second.frame) == len(first.frame)


def test_history_window_covers_200_day_average():
    assert prices.history_days(30) >= 400 and prices.history_days(1825) == 2125


# --------------------------------------------------------------------- news

def _fnspid_csv(path):
    """Mimics FNSPID's Stock_news CSV."""
    pd.DataFrame({
        "Date": ["2020-06-05 06:30:54 UTC", "2020-06-06 09:00:00 UTC", "2020-06-06 09:00:00 UTC", "2020-07-01 12:00:00 UTC", "bad date"],
        "Article_title": ["Apple unveils new chip for Macs", "Tesla deliveries beat expectations", "Tesla deliveries beat expectations",
                          "Apple faces antitrust lawsuit in Europe", "Apple something with a bad date"],
        "Stock_symbol": ["AAPL", "TSLA", "TSLA", "AAPL", "AAPL"],
        "Url": "x", "Publisher": "p", "Author": "a", "Article": "body", "Lsa_summary": "s",
    }).to_csv(path, index=False)


def test_fnspid_loader_filters_dedupes_and_caches():
    root = settings.DATA_DIR / "raw" / "fnspid"
    root.mkdir(parents=True)
    _fnspid_csv(root / "nasdaq_exteral_data.csv")

    df = news.load_fnspid("aapl")
    assert list(df["title"]) == ["Apple unveils new chip for Macs", "Apple faces antitrust lawsuit in Europe"]
    assert df["date"].is_monotonic_increasing and df["date"].dt.tz is None  # bad date dropped
    assert (settings.DATA_DIR / "cache" / "news" / "fnspid_AAPL.csv").exists()
    assert list(news.load_fnspid("AAPL")["title"]) == list(df["title"])  # second read via cache

    assert len(news.load_fnspid("TSLA")) == 1
    with pytest.raises(DataUnavailable):
        news.load_fnspid("MSFT")


def test_fnspid_with_unexpected_columns_is_skipped_not_fatal():
    root = settings.DATA_DIR / "raw" / "fnspid"
    root.mkdir(parents=True)
    pd.DataFrame({"foo": [1], "bar": [2]}).to_csv(root / "other.csv", index=False)
    with pytest.raises(DataUnavailable):
        news.load_fnspid("AAPL")


def test_fnspid_missing_is_a_clean_error():
    with pytest.raises(DataUnavailable, match="not downloaded"):
        news.load_fnspid("AAPL")


def test_company_aliases():
    assert news.aliases("Reliance Industries Limited", "RELIANCE", "NSE") == ["Reliance Industries", "RELIANCE"]
    assert news.aliases("HDFC Bank Ltd.", "500180", "BSE") == ["HDFC Bank"]
    assert news.aliases("Apple Inc.", "AAPL", "NASDAQ") == ["Apple"]


def test_indian_news_matches_company_names_on_word_boundaries():
    root = settings.DATA_DIR / "raw" / "indian_financial_news"
    root.mkdir(parents=True)
    pd.DataFrame({
        "Title": ["ITC reports strong quarterly profit growth", "Pitch perfect results for cricket fans in India",
                  "Markets rally as banks lead gains today", "Sensex climbs on foreign inflows today"],
        "Content": ["x", "the pitch was in good condition", "Reliance Industries shares rose", "nothing relevant"],
        "Date": ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    }).to_csv(root / "news.csv", index=False)

    itc = news.load_indian_news("ITC", "ITC Limited", "NSE")
    assert list(itc["title"]) == ["ITC reports strong quarterly profit growth"]  # "pitch" must not match

    ril = news.load_indian_news("RELIANCE", "Reliance Industries Limited", "NSE")
    assert list(ril["title"]) == ["Markets rally as banks lead gains today"]  # matched via the article body

    with pytest.raises(DataUnavailable):
        news.load_indian_news("TCS", "Tata Consultancy Services Limited", "NSE")


def test_get_news_merges_sources_and_fails_only_when_all_fail(monkeypatch):
    root = settings.DATA_DIR / "raw" / "fnspid"
    root.mkdir(parents=True)
    _fnspid_csv(root / "a.csv")

    def no_live(symbol):
        raise DataUnavailable("offline")

    monkeypatch.setattr(news, "fetch_live_news", no_live)
    got = helpers.REAL_GET_NEWS("NASDAQ", "AAPL", "Apple Inc.")
    assert len(got.frame) == 2 and "FNSPID" in got.sources[0]

    live = pd.DataFrame({"date": [pd.Timestamp("2026-11-01")], "title": ["Apple announces record quarter today"]})
    monkeypatch.setattr(news, "fetch_live_news", lambda symbol: live)
    got = helpers.REAL_GET_NEWS("NASDAQ", "AAPL", "Apple Inc.")
    assert len(got.frame) == 3 and got.frame["date"].is_monotonic_increasing and len(got.sources) == 2

    monkeypatch.setattr(news, "fetch_live_news", no_live)
    with pytest.raises(DataUnavailable, match="No news available"):  # no Indian dataset + no live news
        helpers.REAL_GET_NEWS("NSE", "TCS", "Tata Consultancy Services Limited")


def test_live_news_handles_old_and_new_yahoo_shapes(monkeypatch):
    class FakeTicker:
        def __init__(self, symbol):
            self.news = [
                {"content": {"title": "New-style headline about the company results", "pubDate": "2026-11-10T10:00:00Z"}},
                {"title": "Old-style headline about the company outlook", "providerPublishTime": 1762765200},
                {"title": "", "providerPublishTime": 1},
                "garbage",
            ]

    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", FakeTicker)
    df = news.fetch_live_news("AAPL")
    assert len(df) == 2 and df["date"].dt.tz is None


# ------------------------------------------------------------- fundamentals

def _fact(end, val, start=None, fp="FY", form="10-K", filed="2024-02-01"):
    e = {"end": end, "val": val, "fp": fp, "form": form, "filed": filed}
    if start:
        e["start"] = start
    return e


def _companyfacts():
    usd = lambda *entries: {"units": {"USD": list(entries)}}
    return {"facts": {"us-gaap": {
        # newest tag has newer data; the old tag stops in 2019 and must lose
        "Revenues": usd(_fact("2019-12-31", 50, "2019-01-01")),
        "RevenueFromContractWithCustomerExcludingAssessedTax": usd(
            _fact("2023-12-31", 1100, "2023-01-01", filed="2024-02-01"),
            _fact("2022-12-31", 1000, "2022-01-01", filed="2023-02-01"),
            _fact("2023-03-31", 270, "2023-01-01", fp="Q1", form="10-Q"),           # quarter: ignored
            _fact("2023-12-31", 1090, "2023-01-01", filed="2024-01-01"),            # superseded by the later filing
            _fact("2023-06-30", 500, "2023-01-01"),                                  # 6-month duration: ignored
        ),
        "NetIncomeLoss": usd(_fact("2023-12-31", 220, "2023-01-01"), _fact("2022-12-31", 150, "2022-01-01")),
        "Assets": usd(_fact("2023-12-31", 2000), _fact("2022-12-31", 1800)),
        "Liabilities": usd(_fact("2023-12-31", 1000)),
        "StockholdersEquity": usd(_fact("2023-12-31", 1000)),
    }}}


def test_parse_companyfacts():
    f = fundamentals.parse_companyfacts(_companyfacts())
    m = f.metrics
    assert f.as_of == "2023-12-31" and "EDGAR" in f.source
    assert m["revenue"] == 1100 and m["revenue_growth"] == pytest.approx(0.10)
    assert m["net_margin"] == pytest.approx(0.20) and m["roe"] == pytest.approx(0.22)
    assert m["liabilities_to_assets"] == pytest.approx(0.5)


def test_parse_companyfacts_empty_raises():
    with pytest.raises(DataUnavailable):
        fundamentals.parse_companyfacts({"facts": {"us-gaap": {}}})


def test_us_fundamentals_prefer_edgar_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "SEC_USER_AGENT", "Student student@example.com")
    monkeypatch.setattr(fundamentals, "get_edgar", lambda t: fundamentals.parse_companyfacts(_companyfacts()))
    assert "EDGAR" in helpers.REAL_GET_FUNDAMENTALS("NASDAQ", "AAPL").source


def test_us_fundamentals_fall_back_to_yahoo_with_a_note(monkeypatch):
    monkeypatch.setattr(fundamentals, "fetch_yf_fundamentals",
                        lambda s: fundamentals.Fundamentals({"net_margin": 0.1}, "Yahoo (fake)"))
    skipped = helpers.REAL_GET_FUNDAMENTALS("NYSE", "JPM")  # SEC_USER_AGENT is empty
    assert any("SEC_USER_AGENT" in n for n in skipped.notes)

    monkeypatch.setattr(settings, "SEC_USER_AGENT", "Student student@example.com")

    def edgar_down(t):
        raise DataUnavailable("EDGAR unreachable")

    monkeypatch.setattr(fundamentals, "get_edgar", edgar_down)
    failed = helpers.REAL_GET_FUNDAMENTALS("NYSE", "JPM")
    assert any("EDGAR unavailable" in n for n in failed.notes)


def test_indian_stocks_use_yahoo_symbols(monkeypatch):
    seen = []
    monkeypatch.setattr(fundamentals, "fetch_yf_fundamentals", lambda s: seen.append(s) or fundamentals.Fundamentals({"roe": 0.2}, "y"))
    helpers.REAL_GET_FUNDAMENTALS("NSE", "TCS")
    helpers.REAL_GET_FUNDAMENTALS("BSE", "500325")
    assert seen == ["TCS.NS", "500325.BO"]


def test_yahoo_fundamentals_mapping(monkeypatch):
    info = {f"k{i}": i for i in range(6)}
    info.update({"trailingPE": 20.5, "profitMargins": 0.18, "returnOnEquity": 0.3, "debtToEquity": 145.0,
                 "revenueGrowth": None, "marketCap": 5e11})

    class FakeTicker:
        def __init__(self, symbol):
            self.info = info

    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", FakeTicker)
    m = fundamentals.fetch_yf_fundamentals("TCS.NS").metrics
    assert m["debt_to_equity"] == pytest.approx(1.45)  # Yahoo gives a percentage
    assert "revenue_growth" not in m and m["trailing_pe"] == 20.5


# -------------------------------------------------------------------- macro

def test_fred_vix_parsing_and_percentile(monkeypatch):
    dates = pd.bdate_range(end="2026-11-12", periods=300)
    values = [str(10 + i * 0.1) for i in range(299)] + ["."]  # FRED marks holidays with "."
    values[-2] = "20.0"
    text = pd.DataFrame({"observation_date": dates.strftime("%Y-%m-%d"), "VIXCLS": values}).to_csv(index=False)

    class Resp:
        def __init__(self, t):
            self.text = t

        def raise_for_status(self):
            pass

    import requests

    monkeypatch.setattr(requests, "get", lambda url, timeout: Resp(text))
    v = macro.fetch_fred_vix()
    assert v.name == "VIX" and v.latest == 20.0 and 0 <= v.percentile <= 1 and v.as_of.startswith("2026-11")


def test_vix_failure_becomes_data_unavailable(monkeypatch):
    import requests

    def boom(url, timeout):
        raise requests.ConnectionError("no internet")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(DataUnavailable):
        macro.fetch_fred_vix()


# ---------------------------------------------------------------- sentiment

def _labelled(n=30):
    pos = [f"Profit surges and revenue beats forecasts, strong growth ahead {i}" for i in range(n)]
    neg = [f"Shares plunge on losses, lawsuit and weak outlook warning {i}" for i in range(n)]
    neu = [f"Company schedules annual general meeting for next month {i}" for i in range(n)]
    return pd.DataFrame({"text": pos + neg + neu, "label": ["positive"] * n + ["negative"] * n + ["neutral"] * n})


def test_train_save_load_and_score(tmp_path):
    import joblib

    model, metrics = sentiment_model.train(_labelled())
    assert metrics["accuracy"] > 0.9 and metrics["macro_f1"] > 0.9
    assert metrics["train_rows"] + metrics["test_rows"] == 90

    path = sentiment_model.model_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    sentiment_model.reset_model_cache()

    scores, method = sentiment_model.score_texts(
        ["Profit surges and revenue beats forecasts", "Shares plunge on losses and lawsuit", "Meeting scheduled for next month"]
    )
    assert "trained" in method
    assert scores[0] > 0.3 and scores[1] < -0.3 and abs(scores[2]) < 0.3


def test_train_rejects_bad_data():
    with pytest.raises(ValueError):
        sentiment_model.train(pd.DataFrame({"text": ["a", "b"], "label": ["positive", "positive"]}))


def test_scoring_without_a_model_uses_keywords():
    scores, method = sentiment_model.score_texts(["Record profit as shares surge", "Fraud probe and heavy losses"])
    assert "fallback" in method and scores[0] > 0 > scores[1]
