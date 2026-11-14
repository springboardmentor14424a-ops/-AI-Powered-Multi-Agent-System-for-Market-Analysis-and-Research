"""Sentiment agent: scores news headlines with the trained classifier (or the keyword
fallback) and averages them over the analysis window."""
import pandas as pd

from ..data.news import NewsData
from ..data.sentiment_model import score_texts
from .base import AgentResult, clip, unavailable

NAME = "Sentiment"
MIN_ARTICLES = 3
MAX_ARTICLES = 300
NEUTRAL_BAND = 0.15  # |score| below this counts as a neutral headline


def analyze(news: NewsData, days: int) -> AgentResult:
    df = news.frame
    if df.empty:
        return unavailable(NAME, "No headlines found.")

    # The offline datasets are historical, so the window ends at the newest article we have.
    newest = df["date"].max()
    window = df[df["date"] >= newest - pd.Timedelta(days=days)].tail(MAX_ARTICLES)
    if len(window) < MIN_ARTICLES:
        return unavailable(NAME, f"Only {len(window)} headline(s) in the window; at least {MIN_ARTICLES} are needed.")

    scores, method = score_texts(window["title"].tolist())
    window = window.assign(score=scores)
    mean = float(window["score"].mean())
    pos = int((window["score"] > NEUTRAL_BAND).sum())
    neg = int((window["score"] < -NEUTRAL_BAND).sum())
    neu = len(window) - pos - neg
    score = clip(mean * 1.5)  # headline averages are mild, so stretch them a little

    points = [
        f"{len(window)} headlines from {window['date'].min():%Y-%m-%d} to {window['date'].max():%Y-%m-%d}: "
        f"{pos} positive, {neu} neutral, {neg} negative (average {mean:+.2f}).",
    ]
    best = window.nlargest(2, "score")
    worst = window.nsmallest(2, "score")
    for _, r in best[best["score"] > NEUTRAL_BAND].iterrows():
        points.append(f"Most positive: \"{r['title'][:110]}\" ({r['score']:+.2f})")
    for _, r in worst[worst["score"] < -NEUTRAL_BAND].iterrows():
        points.append(f"Most negative: \"{r['title'][:110]}\" ({r['score']:+.2f})")

    warnings = []
    age = (pd.Timestamp.today().normalize() - newest.normalize()).days
    if age > 30:
        warnings.append(f"The newest headline is from {newest:%Y-%m-%d} ({age} days ago), so this sentiment reflects that period, not today.")
    if "fallback" in method:
        warnings.append("Scored with a simple keyword list. Run scripts/train_sentiment.py for the trained model.")

    label = "Positive" if score > 0.15 else "Negative" if score < -0.15 else "Mixed"
    return AgentResult(NAME, score, label, points, list(news.sources) + [f"Scoring: {method}"], warnings,
                       {"articles": len(window), "positive": pos, "neutral": neu, "negative": neg, "mean": mean})
