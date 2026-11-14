"""Data layer: one module per kind of data, each with offline fallbacks.

  prices.py        Yahoo Finance (yfinance)  ->  Kaggle NIFTY-50 CSVs (NSE, offline)
  news.py          FNSPID (US) / Indian_Financial_News (NSE, BSE)  +  live Yahoo headlines
  fundamentals.py  SEC EDGAR companyfacts (US)  ->  Yahoo Finance fundamentals
  macro.py         FRED VIXCLS (US)  /  India VIX via Yahoo Finance
  sentiment_model.py  classifier trained on Financial PhraseBank + FiQA + Twitter news

Downloaded datasets live under settings.DATA_DIR (default backend/data/):
  raw/      files fetched by scripts/download_data.py
  cache/    derived/cached files, safe to delete
  models/   trained sentiment model
"""
from pathlib import Path

from ..config import settings


class DataUnavailable(Exception):
    """A dataset or data provider couldn't supply what was asked for."""


def data_dir(*parts: str) -> Path:
    # Read settings at call time so tests can point DATA_DIR at a temp folder.
    return Path(settings.DATA_DIR).joinpath(*parts)
