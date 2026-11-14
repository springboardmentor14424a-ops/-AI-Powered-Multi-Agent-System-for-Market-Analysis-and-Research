"""Train the headline-sentiment model used by the Sentiment agent.

    python -m scripts.download_data sentiment     # get the labelled data first
    python -m scripts.train_sentiment

Reads every CSV under data/raw/sentiment/ (columns: text, label where label is
negative / neutral / positive), trains a TF-IDF + logistic-regression classifier on 80%,
reports accuracy on the held-out 20%, and saves data/models/sentiment.joblib.
It trains in seconds on an ordinary laptop CPU. Restart the backend afterwards.
"""
import json
import os
import sys

os.environ.setdefault("JWT_SECRET", "train-script-placeholder-secret-00000000")

import pandas as pd  # noqa: E402

from app.data import data_dir  # noqa: E402
from app.data.sentiment_model import LABELS, model_path, train  # noqa: E402


def load_labelled() -> tuple[pd.DataFrame, dict]:
    """All labelled rows from data/raw/sentiment/**/*.csv, plus rows per source file."""
    root = data_dir("raw", "sentiment")
    frames, per_file = [], {}
    for path in sorted(root.rglob("*.csv")) if root.exists() else []:
        df = pd.read_csv(path)
        df.columns = [c.strip().lower() for c in df.columns]
        if not {"text", "label"} <= set(df.columns):
            print(f"  skipping {path.name}: needs 'text' and 'label' columns")
            continue
        df = df[["text", "label"]].dropna()
        df["label"] = df["label"].astype(str).str.strip().str.lower()
        df = df[df["label"].isin(LABELS)]
        per_file[path.name] = len(df)
        frames.append(df)
    if not frames:
        raise SystemExit(
            f"No labelled data found in {root}\nRun first:  python -m scripts.download_data sentiment"
        )
    return pd.concat(frames, ignore_index=True), per_file


def run_training() -> dict:
    import joblib

    df, per_file = load_labelled()
    print("Training data:")
    for name, n in per_file.items():
        print(f"  {name:<40} {n:>7,} rows")
    model, metrics = train(df)
    metrics["sources"] = per_file

    path = model_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    (path.parent / "sentiment_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nHeld-out accuracy: {metrics['accuracy']:.1%}   macro-F1: {metrics['macro_f1']:.3f}")
    print(f"Saved model -> {path}\nRestart the backend so it picks up the new model.")
    return metrics


if __name__ == "__main__":
    sys.exit(0 if run_training() else 1)
