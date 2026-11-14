"""Tests for the pure logic in the download/training scripts (the network calls
themselves can't be tested offline)."""
import json

import pandas as pd
import pytest

from app.config import settings
from scripts import download_data as dl
from scripts import train_sentiment as tr


def test_label_mappings_match_the_datasets():
    assert [dl.phrasebank_label(i) for i in (0, 1, 2)] == ["negative", "neutral", "positive"]
    assert [dl.twitter_label(i) for i in (0, 1, 2)] == ["negative", "positive", "neutral"]  # Bearish, Bullish, Neutral
    assert dl.fiqa_label(0.6) == "positive" and dl.fiqa_label(-0.4) == "negative" and dl.fiqa_label(0.05) == "neutral"


def test_save_sentiment_cleans_and_dedupes():
    path = dl.save_sentiment("unit", ["Good news today", "Good news today", "  ", "x", "Bad news today"], ["positive", "positive", "neutral", "neutral", "negative"])
    df = pd.read_csv(path)
    assert list(df["text"]) == ["Good news today", "Bad news today"]  # dupe, blank and too-short rows dropped
    assert path.parent == settings.DATA_DIR / "raw" / "sentiment"


def test_stream_filter_keeps_only_wanted_tickers(tmp_path):
    rows = [
        {"Date": "2020-01-01", "Article_title": "Apple does a thing", "Stock_symbol": "AAPL"},
        {"Date": "2020-01-02", "Article_title": "Other company news", "Stock_symbol": "ZZZ"},
        {"Date": "2020-01-03", "Article_title": "", "Stock_symbol": "AAPL"},          # no title: dropped
        {"Date": "2020-01-04", "Article_title": "Tesla does a thing", "Stock_symbol": "tsla"},
        {"Date": "2020-01-05", "Article_title": "Never reached", "Stock_symbol": "AAPL"},
    ]
    out = tmp_path / "f.csv"
    kept, scanned = dl.stream_filter(iter(rows), {"AAPL", "TSLA"}, out, max_rows=4)
    assert (kept, scanned) == (2, 4)
    df = pd.read_csv(out)
    assert list(df["Stock_symbol"]) == ["AAPL", "TSLA"]


def test_status_reports_what_is_on_disk():
    assert all(v["files"] == 0 for v in dl.status().values())
    dl.save_sentiment("unit", ["Good news today"], ["positive"])
    assert dl.status()["sentiment training data"]["files"] == 1


def test_a_downloaded_fnspid_file_is_usable_by_the_loader():
    """What stream_filter writes must be exactly what the news loader reads."""
    from app.data import news

    out = settings.DATA_DIR / "raw" / "fnspid" / "fnspid_filtered.csv"
    dl.stream_filter(iter([{"Date": "2020-06-05 06:30:54 UTC", "Article_title": "Apple unveils new chip for Macs", "Stock_symbol": "AAPL"}]), {"AAPL"}, out)
    assert list(news.load_fnspid("AAPL")["title"]) == ["Apple unveils new chip for Macs"]


def test_training_script_end_to_end():
    pos = [f"Profit surges and revenue beats forecasts, strong growth {i}" for i in range(25)]
    neg = [f"Shares plunge on losses, lawsuit and weak outlook {i}" for i in range(25)]
    neu = [f"Company schedules its annual general meeting {i}" for i in range(25)]
    dl.save_sentiment("a", pos[:12] + neg[:12] + neu[:12], ["positive"] * 12 + ["negative"] * 12 + ["neutral"] * 12)
    dl.save_sentiment("b", pos[12:] + neg[12:] + neu[12:], ["positive"] * 13 + ["negative"] * 13 + ["neutral"] * 13)
    custom = settings.DATA_DIR / "raw" / "sentiment" / "custom"
    custom.mkdir()
    pd.DataFrame({"Text": ["Strong profit growth announced today"], "Label": ["POSITIVE"]}).to_csv(custom / "mine.csv", index=False)  # header/case tolerant
    pd.DataFrame({"foo": [1]}).to_csv(custom / "ignored.csv", index=False)                                                        # wrong schema: skipped

    metrics = tr.run_training()
    assert metrics["accuracy"] > 0.9 and set(metrics["sources"]) == {"a.csv", "b.csv", "mine.csv"}
    model_file = settings.DATA_DIR / "models" / "sentiment.joblib"
    assert model_file.exists()
    assert json.loads((model_file.parent / "sentiment_metrics.json").read_text())["train_rows"] > 0

    from app.data import sentiment_model

    sentiment_model.reset_model_cache()
    scores, method = sentiment_model.score_texts(["Profit surges and revenue beats forecasts", "Shares plunge on losses and lawsuit"])
    assert "trained" in method and scores[0] > 0 > scores[1]


def test_training_without_data_explains_what_to_do():
    with pytest.raises(SystemExit) as e:
        tr.load_labelled()
    assert "download_data sentiment" in str(e.value)
