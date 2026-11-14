"""Headline sentiment: a TF-IDF + logistic-regression classifier trained by
scripts/train_sentiment.py on Financial PhraseBank, FiQA and Twitter financial news.
If no trained model exists yet, a small keyword lexicon is used so the agent still works."""
import logging
import re

import pandas as pd

from . import data_dir

log = logging.getLogger(__name__)

LABELS = ["negative", "neutral", "positive"]
_model = None
_model_loaded = False


def model_path():
    return data_dir("models", "sentiment.joblib")


def load_model():
    """The trained pipeline, or None. Loaded once per process."""
    global _model, _model_loaded
    if not _model_loaded:
        _model_loaded = True
        path = model_path()
        if path.exists():
            try:
                import joblib

                _model = joblib.load(path)
            except Exception:
                log.exception("Could not load sentiment model at %s", path)
    return _model


def reset_model_cache() -> None:
    global _model, _model_loaded
    _model, _model_loaded = None, False


# ----------------------------------------------------------- keyword fallback

_POSITIVE = {
    "beat", "beats", "surge", "surges", "soar", "soars", "jump", "jumps", "rally", "rallies", "gain", "gains",
    "growth", "profit", "profits", "record", "upgrade", "upgrades", "outperform", "strong", "boost", "raises",
    "rises", "rise", "expands", "wins", "approval", "approved", "dividend", "buyback", "bullish", "optimistic",
}
_NEGATIVE = {
    "miss", "misses", "fall", "falls", "drop", "drops", "plunge", "plunges", "slump", "slumps", "loss", "losses",
    "downgrade", "downgrades", "lawsuit", "probe", "fraud", "weak", "cut", "cuts", "decline", "declines",
    "recall", "layoffs", "warns", "warning", "bearish", "default", "penalty", "fine", "investigation", "debt",
}
_WORDS = re.compile(r"[a-z]+")


def lexicon_score(text: str) -> float:
    words = _WORDS.findall(text.lower())
    pos = sum(w in _POSITIVE for w in words)
    neg = sum(w in _NEGATIVE for w in words)
    return 0.0 if pos + neg == 0 else (pos - neg) / (pos + neg)


# -------------------------------------------------------------------- scoring

def score_texts(texts: list[str]) -> tuple[list[float], str]:
    """Sentiment per text in [-1, 1] (P(positive) - P(negative)) and a method label."""
    model = load_model()
    if model is None:
        return [lexicon_score(t) for t in texts], "keyword fallback (train the model for better accuracy)"
    proba = model.predict_proba(texts)
    classes = list(model.classes_)
    pos, neg = classes.index("positive"), classes.index("negative")
    return [float(p[pos] - p[neg]) for p in proba], "trained TF-IDF + logistic regression model"


# ------------------------------------------------------------------- training

def train(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> tuple[object, dict]:
    """Fit on a DataFrame with columns text and label (negative/neutral/positive).
    Returns (fitted pipeline, metrics dict)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    df = df.dropna(subset=["text", "label"]).drop_duplicates("text")
    df = df[df["label"].isin(LABELS)]
    if df["label"].nunique() < 2 or len(df) < 10:
        raise ValueError("Need at least 10 labelled rows covering 2+ classes to train.")

    x_train, x_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=test_size, random_state=seed,
        stratify=df["label"] if df["label"].value_counts().min() >= 2 else None,
    )
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
    ])
    pipe.fit(x_train, y_train)
    pred = pipe.predict(x_test)
    metrics = {
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
        "class_counts": {k: int(v) for k, v in df["label"].value_counts().items()},
    }
    return pipe, metrics
