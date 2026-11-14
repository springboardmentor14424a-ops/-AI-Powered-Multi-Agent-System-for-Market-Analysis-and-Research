"""News headlines for the sentiment agent.

US stocks     FNSPID (offline dataset)                       + live Yahoo headlines
NSE / BSE     kdave/Indian_Financial_News (offline dataset)  + live Yahoo headlines

The offline datasets are historical, so the sentiment agent reports the date range it
actually used. Raises DataUnavailable when no source has anything.
"""
import logging
import re
from dataclasses import dataclass, field

import pandas as pd

from ..stocks import provider_symbol
from . import DataUnavailable, data_dir

log = logging.getLogger(__name__)


@dataclass
class NewsData:
    frame: pd.DataFrame  # columns: date (tz-naive datetime), title; sorted by date
    sources: list[str] = field(default_factory=list)


def _pick(columns, candidates) -> str | None:
    """Case-insensitive first match, so small schema differences don't break loading."""
    lowered = {str(c).lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    return None


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_localize(None)
    df["title"] = df["title"].astype(str).str.strip()
    df = df.dropna(subset=["date"])
    df = df[df["title"].str.len() > 10]
    return df.drop_duplicates("title").sort_values("date")[["date", "title"]].reset_index(drop=True)


# ---------------------------------------------------------------- FNSPID (US)

def load_fnspid(ticker: str) -> pd.DataFrame:
    root = data_dir("raw", "fnspid")
    files = sorted(root.rglob("*.csv")) if root.exists() else []
    if not files:
        raise DataUnavailable("FNSPID is not downloaded (run scripts/download_data.py news)")

    cache = data_dir("cache", "news", f"fnspid_{ticker.upper()}.csv")
    newest_raw = max(f.stat().st_mtime for f in files)
    if cache.exists() and cache.stat().st_mtime >= newest_raw:
        return _finish(pd.read_csv(cache))

    parts = []
    for f in files:
        cols = pd.read_csv(f, nrows=0).columns
        sym = _pick(cols, ["Stock_symbol", "symbol", "ticker"])
        title = _pick(cols, ["Article_title", "title", "headline"])
        date = _pick(cols, ["Date", "date", "published"])
        if not (sym and title and date):
            log.warning("Skipping %s: expected symbol/title/date columns, found %s", f.name, list(cols))
            continue
        # Big files are read in chunks so memory stays small.
        for chunk in pd.read_csv(f, usecols=[sym, title, date], chunksize=200_000, dtype=str, on_bad_lines="skip"):
            hit = chunk[chunk[sym].str.upper().str.strip() == ticker.upper()]
            if not hit.empty:
                parts.append(hit.rename(columns={title: "title", date: "date"})[["date", "title"]])
    if not parts:
        raise DataUnavailable(f"No FNSPID articles found for {ticker}")

    df = _finish(pd.concat(parts, ignore_index=True))
    if df.empty:
        raise DataUnavailable(f"No usable FNSPID articles for {ticker}")
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache, index=False)  # next time we skip scanning the big file
    except OSError:
        pass
    return df


# --------------------------------------------------- Indian_Financial_News (NSE/BSE)

_LEGAL_SUFFIXES = re.compile(r"\b(limited|ltd|inc|corporation|corp|company|co|plc|the)\b", re.IGNORECASE)


def aliases(company_name: str, ticker: str, market: str) -> list[str]:
    """Names a news article might use for this company ("Reliance Industries Limited"
    -> "Reliance Industries"), plus the NSE symbol when it's distinctive enough."""
    base = _LEGAL_SUFFIXES.sub(" ", re.sub(r"[,.]", " ", company_name))
    base = " ".join(base.split())
    found = {base} if len(base) >= 3 else set()
    if market == "NSE" and len(ticker) >= 3:
        found.add(ticker)
    return sorted(found, key=len, reverse=True)


def load_indian_news(ticker: str, company_name: str, market: str) -> pd.DataFrame:
    root = data_dir("raw", "indian_financial_news")
    files = [p for p in sorted(root.rglob("*")) if p.suffix in {".csv", ".parquet"}] if root.exists() else []
    if not files:
        raise DataUnavailable("Indian_Financial_News is not downloaded (run scripts/download_data.py news)")
    names = aliases(company_name, ticker, market)
    if not names:
        raise DataUnavailable("Company name too short to search the Indian news dataset")
    pattern = r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\b"

    parts = []
    for f in files:
        df = pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_csv(f, dtype=str, on_bad_lines="skip")
        title = _pick(df.columns, ["Title", "headline", "Headline"])
        date = _pick(df.columns, ["Date", "published", "publishedAt", "pubDate", "Time"])
        body = _pick(df.columns, ["Content", "Description", "Summary", "Text"])
        if not (title and date):
            log.warning("Skipping %s: no title/date columns (found %s)", f.name, list(df.columns))
            continue
        haystack = df[title].fillna("").astype(str)
        if body:
            haystack = haystack + " " + df[body].fillna("").astype(str)
        hit = df[haystack.str.contains(pattern, flags=re.IGNORECASE, regex=True)]
        if not hit.empty:
            parts.append(hit.rename(columns={title: "title", date: "date"})[["date", "title"]])
    if not parts:
        raise DataUnavailable(f"No articles mentioning {company_name} in the Indian news dataset")
    out = _finish(pd.concat(parts, ignore_index=True))
    if out.empty:
        raise DataUnavailable(f"No usable Indian news articles for {company_name}")
    return out


# ------------------------------------------------------------- live headlines

def fetch_live_news(symbol: str) -> pd.DataFrame:
    """Recent headlines from Yahoo Finance. Handles both the old and new response shapes."""
    try:
        import yfinance as yf

        items = yf.Ticker(symbol).news or []
    except Exception as e:
        log.warning("Yahoo Finance news request failed for %s: %s", symbol, e)
        raise DataUnavailable("Could not download live headlines from Yahoo Finance.") from e
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        content = item.get("content") if isinstance(item.get("content"), dict) else None
        if content:
            title, when = content.get("title"), content.get("pubDate") or content.get("displayTime")
        else:
            title, when = item.get("title"), item.get("providerPublishTime")
            if isinstance(when, (int, float)):
                when = pd.to_datetime(when, unit="s", utc=True)
        if title and when is not None:
            rows.append({"date": when, "title": title})
    if not rows:
        raise DataUnavailable("Yahoo Finance returned no headlines")
    df = _finish(pd.DataFrame(rows))
    if df.empty:
        raise DataUnavailable("Yahoo Finance returned no usable headlines")
    return df


# ---------------------------------------------------------------------- entry

def get_news(market: str, ticker: str, company_name: str) -> NewsData:
    frames, sources, problems = [], [], []

    try:
        if market in ("NASDAQ", "NYSE"):
            df = load_fnspid(ticker)
            sources.append(f"FNSPID dataset ({len(df)} articles, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d})")
        else:
            df = load_indian_news(ticker, company_name, market)
            sources.append(f"Indian_Financial_News dataset ({len(df)} articles, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d})")
        frames.append(df)
    except DataUnavailable as e:
        problems.append(str(e))

    try:
        df = fetch_live_news(provider_symbol(market, ticker))
        frames.append(df)
        sources.append(f"Yahoo Finance live headlines ({len(df)})")
    except DataUnavailable as e:
        problems.append(str(e))

    if not frames:
        raise DataUnavailable("No news available: " + "; ".join(p.rstrip(".") for p in problems) + ".")
    merged = pd.concat(frames, ignore_index=True).drop_duplicates("title").sort_values("date")
    return NewsData(merged.reset_index(drop=True), sources)
