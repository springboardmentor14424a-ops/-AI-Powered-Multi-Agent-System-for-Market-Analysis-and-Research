import math
from datetime import datetime, timezone
from typing import Any
import yfinance as yf

MARKET_ALIASES = {
    "NSE": "NSE",
    "NS": "NSE",
    "BSE": "BSE",
    "BO": "BSE",
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE",
}

PERIOD_MAP = {
    "1 MONTH": ("1 Month", "1mo", "1d"),
    "1MO": ("1 Month", "1mo", "1d"),
    "3 MONTHS": ("3 Months", "3mo", "1d"),
    "3MO": ("3 Months", "3mo", "1d"),
    "6 MONTHS": ("6 Months", "6mo", "1d"),
    "6MO": ("6 Months", "6mo", "1d"),
    "1 YEAR": ("1 Year", "1y", "1d"),
    "1Y": ("1 Year", "1y", "1d"),
    "5 YEARS": ("5 Years", "5y", "1wk"),
    "5Y": ("5 Years", "5y", "1wk"),
}


def _safe_round(value: Any, digits: int = 2) -> float | None:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return round(num, digits)


def normalize_market(market: str | None) -> str:
    cleaned = (market or "NASDAQ").strip().upper()
    if cleaned not in MARKET_ALIASES:
        raise ValueError(
            f"Unsupported market '{market}'. Expected one of: NSE, BSE, NASDAQ, NYSE."
        )
    return MARKET_ALIASES[cleaned]


def normalize_period(period: str | None) -> tuple[str, str]:
    cleaned = (period or "1 Year").strip().upper()
    if cleaned not in PERIOD_MAP:
        raise ValueError(
            f"Unsupported analysis period '{period}'. Expected one of: 1 Month, 3 Months, 6 Months, 1 Year, 5 Years."
        )
    label, yf_period, _ = PERIOD_MAP[cleaned]
    return label, yf_period


def format_ticker_for_market(symbol: str, market: str) -> str:
    raw = (symbol or "").strip().upper()
    if not raw:
        raise ValueError("Ticker symbol cannot be empty.")

    base = raw
    for suffix in (".NS", ".BO"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]

    if market == "NSE":
        return f"{base}.NS"
    if market == "BSE":
        return f"{base}.BO"
    return base


def format_yahoo_ticker(symbol: str, market: str) -> str:
    return format_ticker_for_market(symbol, market)


def search_companies(query: str, market: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    norm_market = normalize_market(market) if market else None
    results: list[dict[str, Any]] = []

    try:
        search_obj = yf.Search(cleaned_query, max_results=max(limit * 2, 10))
        quotes = getattr(search_obj, "quotes", None) or []
        for item in quotes:
            if not isinstance(item, dict):
                continue
            raw_symbol = str(item.get("symbol") or "").strip().upper()
            if not raw_symbol:
                continue

            exchange = str(item.get("exchange") or item.get("exchDisp") or "").upper()
            inferred_market = (
                "NSE"
                if raw_symbol.endswith(".NS") or "NSI" in exchange or "NSE" in exchange
                else "BSE"
                if raw_symbol.endswith(".BO") or "BSE" in exchange or "BOM" in exchange
                else "NYSE"
                if "NYQ" in exchange or "NYSE" in exchange
                else "NASDAQ"
            )

            if norm_market and inferred_market != norm_market:
                continue

            clean_ticker = raw_symbol.removesuffix(".NS").removesuffix(".BO")
            company_name = (
                item.get("longname")
                or item.get("shortname")
                or item.get("name")
                or clean_ticker
            )

            results.append(
                {
                    "ticker": clean_ticker,
                    "symbol": raw_symbol,
                    "company_name": company_name,
                    "market": inferred_market,
                    "exchange": item.get("exchDisp") or exchange or inferred_market,
                }
            )
            if len(results) >= limit:
                break
    except Exception:
        pass

    return results


def fetch_market_bundle(
    symbol: str,
    market: str = "NASDAQ",
    period: str = "1 Year",
) -> dict[str, Any]:
    norm_market = normalize_market(market)
    period_label, _ = normalize_period(period)
    _, yf_period, yf_interval = PERIOD_MAP[period_label.upper()]
    yahoo_symbol = format_ticker_for_market(symbol, norm_market)
    clean_symbol = yahoo_symbol.removesuffix(".NS").removesuffix(".BO")

    ticker_obj = yf.Ticker(yahoo_symbol)
    hist = ticker_obj.history(period=yf_period, interval=yf_interval, auto_adjust=False)

    if hist is None or hist.empty:
        raise ValueError(
            f"No historical OHLCV data returned from Yahoo Finance for '{yahoo_symbol}' ({norm_market}, {period_label})."
        )

    hist = hist.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if hist.empty:
        raise ValueError(f"OHLCV rows for '{yahoo_symbol}' contained only missing prices.")

    warnings: list[str] = []
    if (hist["Close"] <= 0).any():
        warnings.append("Non-positive close prices detected in series.")
    if (hist["High"] < hist["Low"]).any():
        warnings.append("Rows where High < Low were detected.")
    if "Volume" in hist.columns and (hist["Volume"] < 0).any():
        warnings.append("Negative volume values detected.")

    closes = hist["Close"].astype(float)
    first_close = float(closes.iloc[0])
    last_close = float(closes.iloc[-1])
    period_high = float(hist["High"].astype(float).max())
    period_low = float(hist["Low"].astype(float).min())
    period_return_pct = ((last_close - first_close) / first_close * 100.0) if first_close else 0.0

    sma_20_series = closes.rolling(window=min(len(closes), 20), min_periods=1).mean()
    sma_50_series = closes.rolling(window=min(len(closes), 50), min_periods=1).mean()
    sma_20 = float(sma_20_series.iloc[-1])
    sma_50 = float(sma_50_series.iloc[-1])
    daily_returns = closes.pct_change().dropna()
    volatility_pct = float(daily_returns.std() * 100.0) if not daily_returns.empty else 0.0
    if not math.isfinite(volatility_pct):
        volatility_pct = 0.0

    step = max(1, len(hist) // 160)
    sampled_indices = list(range(0, len(hist), step))
    if sampled_indices[-1] != len(hist) - 1:
        sampled_indices.append(len(hist) - 1)

    chart_series: list[dict[str, Any]] = []
    for idx in sampled_indices:
        dt_label = hist.index[idx].strftime("%Y-%m-%d")
        vol_val = 0
        if "Volume" in hist.columns:
            raw_vol = _safe_round(hist["Volume"].iloc[idx], 0)
            vol_val = int(raw_vol) if raw_vol is not None else 0

        close_val = _safe_round(closes.iloc[idx], 2) or 0.0
        s20_val = _safe_round(sma_20_series.iloc[idx], 2)
        s50_val = _safe_round(sma_50_series.iloc[idx], 2)

        chart_series.append(
            {
                "date": dt_label,
                "close": close_val,
                "sma_20": s20_val if s20_val is not None else close_val,
                "sma_50": s50_val if s50_val is not None else close_val,
                "volume": vol_val,
            }
        )

    info: dict[str, Any] = {}
    try:
        raw_info = ticker_obj.info
        if isinstance(raw_info, dict):
            info = raw_info
    except Exception:
        warnings.append("Company metadata lookup partially unavailable; using OHLCV metrics.")

    default_currency = "INR" if norm_market in ("NSE", "BSE") else "USD"
    company_name = (
        info.get("longName")
        or info.get("shortName")
        or clean_symbol
    )

    raw_summary = info.get("longBusinessSummary") or info.get("description") or ""
    short_summary = (
        raw_summary[:260].rsplit(" ", 1)[0] + "..."
        if len(raw_summary) > 260
        else raw_summary
    )

    start_date = hist.index[0].strftime("%Y-%m-%d")
    end_date = hist.index[-1].strftime("%Y-%m-%d")

    return {
        "ticker": clean_symbol,
        "symbol": yahoo_symbol,
        "market": norm_market,
        "analysis_period": period_label,
        "source": "Yahoo Finance (yfinance)",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "company_name": company_name,
            "sector": info.get("sector") or "N/A",
            "industry": info.get("industry") or "N/A",
            "exchange": info.get("exchange") or info.get("exchDisp") or norm_market,
            "currency": info.get("currency") or default_currency,
            "market_cap": info.get("marketCap"),
            "pe_ratio": _safe_round(info.get("trailingPE"), 2),
            "week_52_high": _safe_round(info.get("fiftyTwoWeekHigh"), 2),
            "week_52_low": _safe_round(info.get("fiftyTwoWeekLow"), 2),
            "summary": short_summary or "Business summary unavailable.",
        },
        "summary_metrics": {
            "latest_close": _safe_round(last_close, 2) or 0.0,
            "period_open": _safe_round(first_close, 2) or 0.0,
            "period_high": _safe_round(period_high, 2) or 0.0,
            "period_low": _safe_round(period_low, 2) or 0.0,
            "period_return_pct": _safe_round(period_return_pct, 2) or 0.0,
            "sma_20": _safe_round(sma_20, 2) or 0.0,
            "sma_50": _safe_round(sma_50, 2) or 0.0,
            "volatility_pct": _safe_round(volatility_pct, 2) or 0.0,
            "rows_count": int(len(hist)),
            "start_date": start_date,
            "end_date": end_date,
        },
        "chart_series": chart_series,
        "validation": {
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
        },
    }


def run_multi_agent_analysis(
    bundle: dict[str, Any],
    risk_tolerance: str = "Moderate",
) -> dict[str, Any]:
    profile = bundle["profile"]
    metrics = bundle["summary_metrics"]
    validation = bundle["validation"]

    company = profile.get("company_name") or bundle["symbol"]
    sector = profile.get("sector") or "N/A"
    industry = profile.get("industry") or "N/A"
    currency = profile.get("currency") or ""
    pe_ratio = profile.get("pe_ratio")

    latest_close = metrics["latest_close"]
    ret_pct = metrics["period_return_pct"]
    sma_20 = metrics["sma_20"]
    sma_50 = metrics["sma_50"]
    vol_pct = metrics["volatility_pct"]

    pe_text = f"Trailing P/E: {round(float(pe_ratio), 2)}" if pe_ratio else "Trailing P/E: N/A"
    fundamental_note = (
        f"{company} operates in {sector} ({industry}) with {pe_text}. "
        f"Latest trading level is {currency} {latest_close} across {metrics['rows_count']} sessions "
        f"({metrics['start_date']} to {metrics['end_date']})."
    )

    trend_stance = "above" if latest_close >= sma_20 else "below"
    ma_cross = "bullish (SMA20 >= SMA50)" if sma_20 >= sma_50 else "bearish (SMA20 < SMA50)"
    technical_note = (
        f"Period return is {ret_pct:+.2f}% with range {currency} {metrics['period_low']}–{currency} {metrics['period_high']}. "
        f"Price is {trend_stance} 20-period SMA ({sma_20}) and momentum structure is {ma_cross} (50-period SMA: {sma_50})."
    )

    risk_level = (risk_tolerance or "Moderate").strip().capitalize()
    warning_text = (
        f"Data flags: {'; '.join(validation['warnings'])}."
        if validation["warnings"]
        else "OHLCV & metadata validation passed cleanly."
    )
    risk_note = (
        f"Session volatility is {vol_pct:.2f}% under a {risk_level} risk profile. {warning_text}"
    )

    if ret_pct >= 12 and vol_pct <= 4.0:
        conviction = "Strong Buy"
    elif ret_pct >= 3:
        conviction = "Accumulate / Bullish"
    elif ret_pct <= -10:
        conviction = "High Caution / Bearish"
    else:
        conviction = "Hold / Neutral"

    cio_summary = (
        f"[{conviction}] {company} ({bundle['symbol']}, {bundle['market']}) posted {ret_pct:+.2f}% over "
        f"{bundle['analysis_period']} ({currency} {latest_close}). {technical_note} {risk_note}"
    )

    return {
        "company_name": company,
        "symbol": bundle["symbol"],
        "market": bundle["market"],
        "analysis_period": bundle["analysis_period"],
        "cio_synthesis": {
            "conviction": conviction,
            "summary": cio_summary[:1990],
        },
        "agents": {
            "fundamental": fundamental_note,
            "technical": technical_note,
            "risk": risk_note,
        },
    }