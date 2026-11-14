"""Download the open datasets used by the app into backend/data/raw/.

Run from the backend folder (with your virtual environment active):

    pip install -r requirements-data.txt        # once: Hugging Face / Kaggle download helpers
    python -m scripts.download_data check       # what is already downloaded
    python -m scripts.download_data sentiment   # Financial PhraseBank + FiQA + Twitter financial news
    python -m scripts.download_data prices      # Kaggle NIFTY-50 (offline NSE prices)
    python -m scripts.download_data news        # Indian_Financial_News + FNSPID (US, streamed and filtered)
    python -m scripts.download_data all

Each step prints what it saved, or exactly what to do by hand if a download fails
(dataset hosts change; any CSV you place in the right folder is picked up automatically).
"""
import argparse
import csv
import os
import shutil
import sys
from pathlib import Path

# The app config insists on a JWT secret; downloading data doesn't need a real one.
os.environ.setdefault("JWT_SECRET", "download-script-placeholder-secret-0000")

import pandas as pd  # noqa: E402

from app.data import data_dir  # noqa: E402
from app.stocks import _STOCKS  # noqa: E402

PHRASEBANK_CONFIG = "sentences_75agree"
FNSPID_REPO = "Zihan1004/FNSPID"
FNSPID_FILE = "Stock_news/nasdaq_exteral_data.csv"


# ------------------------------------------------------------- label mapping

def phrasebank_label(i: int) -> str:
    return {0: "negative", 1: "neutral", 2: "positive"}[int(i)]


def twitter_label(i: int) -> str:
    return {0: "negative", 1: "positive", 2: "neutral"}[int(i)]  # Bearish / Bullish / Neutral


def fiqa_label(score: float) -> str:
    score = float(score)
    return "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"


def _first(columns, candidates):
    return next((c for c in candidates if c in columns), None)


def save_sentiment(name: str, texts, labels) -> Path:
    df = pd.DataFrame({"text": list(texts), "label": list(labels)}).dropna()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 3].drop_duplicates("text")
    path = data_dir("raw", "sentiment", f"{name}.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  saved {len(df):,} rows -> {path}  ({df['label'].value_counts().to_dict()})")
    return path


def _all_splits(ds) -> pd.DataFrame:
    return pd.concat([ds[s].to_pandas() for s in ds.keys()], ignore_index=True)


def _manual(what: str, where: str, how: str) -> None:
    print(f"  ! could not download {what} automatically.\n    Do it by hand: {how}\n    Put the file(s) in: {where}")


# ---------------------------------------------------------------- sentiment

def download_sentiment() -> None:
    from datasets import load_dataset

    print("Financial PhraseBank (labelled sentences, CC BY-NC-SA: non-commercial use)")
    try:
        try:
            ds = load_dataset("takala/financial_phrasebank", PHRASEBANK_CONFIG, trust_remote_code=True)
        except Exception:
            ds = load_dataset("financial_phrasebank", PHRASEBANK_CONFIG, trust_remote_code=True)
        df = _all_splits(ds)
        save_sentiment("financial_phrasebank", df["sentence"], df["label"].map(phrasebank_label))
    except Exception as e:
        print(f"  error: {e}")
        _manual("Financial PhraseBank", str(data_dir("raw", "sentiment", "custom")),
                "get 'takala/financial_phrasebank' from huggingface.co and save a CSV with columns text,label "
                "(label = negative / neutral / positive)")

    print("FiQA financial sentiment")
    try:
        df = _all_splits(load_dataset("pauri32/fiqa-pa"))
        text = _first(df.columns, ["sentence", "text", "snippet"])
        score = _first(df.columns, ["sentiment_score", "score"])
        save_sentiment("fiqa", df[text], df[score].map(fiqa_label))
    except Exception as e:
        print(f"  error: {e}")
        _manual("FiQA", str(data_dir("raw", "sentiment", "custom")), "get 'pauri32/fiqa-pa' from huggingface.co and save text,label as above")

    print("Twitter financial news sentiment")
    try:
        df = _all_splits(load_dataset("zeroshot/twitter-financial-news-sentiment"))
        save_sentiment("twitter_financial_news", df["text"], df["label"].map(twitter_label))
    except Exception as e:
        print(f"  error: {e}")
        _manual("Twitter financial news", str(data_dir("raw", "sentiment", "custom")),
                "get 'zeroshot/twitter-financial-news-sentiment' from huggingface.co and save text,label as above")


# ------------------------------------------------------------------- prices

def download_prices() -> None:
    print("Kaggle NIFTY-50 Stock Market Data (rohanrao), used as an offline NSE price fallback")
    dest = data_dir("raw", "nifty50")
    try:
        import kagglehub

        src = Path(kagglehub.dataset_download("rohanrao/nifty50-stock-market-data"))
        dest.mkdir(parents=True, exist_ok=True)
        files = [p for p in src.rglob("*.csv")]
        for p in files:
            shutil.copy2(p, dest / p.name)
        print(f"  copied {len(files)} CSV files -> {dest}")
    except Exception as e:
        print(f"  error: {e}")
        _manual("the NIFTY-50 dataset", str(dest),
                "open kaggle.com/datasets/rohanrao/nifty50-stock-market-data, click Download, unzip the CSVs "
                "(RELIANCE.csv, TCS.csv, ...). A free Kaggle login may be needed")


# --------------------------------------------------------------------- news

def stream_filter(rows, wanted: set[str], out_path: Path, max_rows: int | None = None) -> tuple[int, int]:
    """Keep only rows whose Stock_symbol is in `wanted`, writing them to a CSV as we go
    (so the multi-GB source is never stored). Returns (rows kept, rows scanned)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kept = scanned = 0
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Article_title", "Stock_symbol"])
        for row in rows:
            scanned += 1
            if scanned % 1_000_000 == 0:
                print(f"  ...scanned {scanned:,} articles, kept {kept:,}")
            if str(row.get("Stock_symbol", "")).upper() in wanted and row.get("Article_title"):
                w.writerow([row.get("Date"), row["Article_title"], str(row["Stock_symbol"]).upper()])
                kept += 1
            if max_rows and scanned >= max_rows:
                break
    return kept, scanned


def download_news(tickers: list[str] | None = None, max_rows: int | None = None) -> None:
    from datasets import load_dataset

    print("Indian_Financial_News (Hugging Face: kdave/Indian_Financial_News)")
    dest = data_dir("raw", "indian_financial_news")
    try:
        df = _all_splits(load_dataset("kdave/Indian_Financial_News"))
        dest.mkdir(parents=True, exist_ok=True)
        df.to_csv(dest / "news.csv", index=False)
        print(f"  saved {len(df):,} articles -> {dest / 'news.csv'}  (columns: {list(df.columns)})")
    except Exception as e:
        print(f"  error: {e}")
        _manual("Indian_Financial_News", str(dest), "download the CSV/parquet from huggingface.co/datasets/kdave/Indian_Financial_News")

    wanted = {t.upper() for t in (tickers or [t for m, t, _ in _STOCKS if m in ("NASDAQ", "NYSE")])}
    print(f"FNSPID (US news, CC BY 4.0): streaming and keeping {len(wanted)} tickers. The source file is several GB,")
    print("  so this reads it without saving it and can take a long time; Ctrl+C is safe, rerun any time.")
    out = data_dir("raw", "fnspid", "fnspid_filtered.csv")
    try:
        ds = load_dataset(FNSPID_REPO, data_files=FNSPID_FILE, split="train", streaming=True)
        kept, scanned = stream_filter(ds, wanted, out, max_rows)
        print(f"  kept {kept:,} of {scanned:,} articles -> {out}")
    except Exception as e:
        print(f"  error: {e}")
        _manual("FNSPID", str(data_dir("raw", "fnspid")),
                f"download {FNSPID_FILE} from huggingface.co/datasets/{FNSPID_REPO} (large) "
                "or keep just the rows for your tickers")


# -------------------------------------------------------------------- check

def status() -> dict:
    """What's on disk, as data (also used by tests)."""
    def folder(*parts, pattern="*.csv"):
        root = data_dir(*parts)
        files = [p for p in root.rglob(pattern)] if root.exists() else []
        return {"files": len(files), "mb": round(sum(p.stat().st_size for p in files) / 1e6, 2), "path": str(root)}

    return {
        "sentiment training data": folder("raw", "sentiment"),
        "NIFTY-50 prices": folder("raw", "nifty50"),
        "Indian_Financial_News": folder("raw", "indian_financial_news", pattern="*.*"),
        "FNSPID news": folder("raw", "fnspid"),
        "trained sentiment model": folder("models", pattern="sentiment.joblib"),
    }


def print_status() -> None:
    from app.config import settings

    print(f"Data folder: {settings.DATA_DIR}\n")
    for name, info in status().items():
        mark = "OK     " if info["files"] else "missing"
        print(f"  [{mark}] {name:<26} {info['files']:>4} file(s), {info['mb']:>9} MB")
    print(f"\n  SEC EDGAR (US fundamentals): {'enabled' if settings.SEC_USER_AGENT else 'off, set SEC_USER_AGENT in .env to enable'}")
    print("  Live prices/news/fundamentals/VIX come from Yahoo Finance and FRED at run time (no download needed).")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["check", "sentiment", "prices", "news", "all"])
    p.add_argument("--tickers", help="comma-separated US tickers to keep from FNSPID (default: the app's US stock list)")
    p.add_argument("--max-rows", type=int, help="stop FNSPID streaming after this many rows (for a quick trial)")
    a = p.parse_args(argv)
    tickers = a.tickers.split(",") if a.tickers else None

    if a.step == "check":
        print_status()
        return 0
    if a.step in ("sentiment", "all"):
        download_sentiment()
    if a.step in ("prices", "all"):
        download_prices()
    if a.step in ("news", "all"):
        download_news(tickers, a.max_rows)
    print()
    print_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
