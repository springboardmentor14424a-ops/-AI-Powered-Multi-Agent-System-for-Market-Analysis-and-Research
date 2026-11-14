"""Market-wide volatility index for the risk agent: VIX (FRED series VIXCLS) for US
stocks, India VIX (Yahoo Finance ^INDIAVIX) for NSE/BSE."""
import io
import logging
from dataclasses import dataclass

import pandas as pd

from ..config import settings
from . import DataUnavailable
from .prices import fetch_live

log = logging.getLogger(__name__)

@dataclass
class VolIndex:
    name: str
    latest: float
    percentile: float  # share of the last ~year of readings at or below the latest (0-1)
    as_of: str
    source: str


def _summarise(name: str, series: pd.Series, source: str) -> VolIndex:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 20:
        raise DataUnavailable(f"Not enough {name} data")
    last = float(s.iloc[-1])
    year = s.iloc[-252:]
    return VolIndex(name, last, float((year <= last).mean()), f"{s.index[-1]:%Y-%m-%d}", source)


def fetch_fred_vix() -> VolIndex:
    try:
        import requests

        r = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS", timeout=settings.HTTP_TIMEOUT
        )
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.index = pd.to_datetime(df.iloc[:, 0])
        series = df["VIXCLS"]
    except Exception as e:
        log.warning("FRED request failed: %s", e)
        raise DataUnavailable("Could not download the VIX from FRED.") from e
    return _summarise("VIX", series, "FRED series VIXCLS")


def fetch_india_vix() -> VolIndex:
    df = fetch_live("^INDIAVIX", 420)
    return _summarise("India VIX", df["close"], "Yahoo Finance ^INDIAVIX")


def get_volatility_index(market: str) -> VolIndex:
    return fetch_fred_vix() if market in ("NASDAQ", "NYSE") else fetch_india_vix()
