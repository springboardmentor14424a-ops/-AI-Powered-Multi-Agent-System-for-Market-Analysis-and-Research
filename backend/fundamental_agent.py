import math
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd

# Curated peer map for reliable peer comparisons across US & Indian markets
PEER_MAP = {
    # US Tech
    "AAPL": ["MSFT", "GOOGL", "META"],
    "MSFT": ["AAPL", "GOOGL", "ORCL"],
    "GOOGL": ["META", "MSFT", "AMZN"],
    "NVDA": ["AMD", "INTC", "AVGO"],
    "TSLA": ["F", "GM", "TM"],
    "AMZN": ["WMT", "MSFT", "GOOGL"],
    # Indian Market (NSE)
    "RELIANCE.NS": ["ONGC.NS", "IOC.NS", "BPCL.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS"],
    "HDFCBANK.NS": ["ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS"],
    "ICICIBANK.NS": ["HDFCBANK.NS", "SBIN.NS", "AXISBANK.NS"],
    "SBIN.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "BANKBARODA.NS"],
}

SECTOR_DEFAULT_PEERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL"],
    "Financial Services": ["JPM", "BAC", "WFC"],
    "Energy": ["XOM", "CVX", "COP"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD"],
    "Healthcare": ["JNJ", "UNH", "PFE"],
}


def _safe_float(val):
    """Convert to float safely; return None if NaN, inf, or invalid."""
    try:
        if val is None or pd.isna(val):
            return None
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 4)
    except Exception:
        return None


def _resolve_symbol(symbol: str, market: str) -> str:
    sym = symbol.strip().upper()
    if "." in sym:
        return sym
    if market == "NSE":
        return f"{sym}.NS"
    if market == "BSE":
        return f"{sym}.BO"
    return sym


def _extract_row_series(df: pd.DataFrame, candidates: list[str]) -> dict:
    """Find the first matching row name in a yfinance financial statement DataFrame."""
    if df is None or df.empty:
        return {}
    for name in candidates:
        if name in df.index:
            series = df.loc[name]
            result = {}
            for col, val in series.items():
                year = str(col)[:4]
                num = _safe_float(val)
                if num is not None:
                    result[year] = num
            return result
    return {}


def _pct_change(latest, previous):
    if latest is None or previous is None or previous == 0:
        return None
    return round(((latest - previous) / abs(previous)) * 100, 2)


def _fetch_peer_snapshot(peer_symbol: str) -> dict | None:
    try:
        t = yf.Ticker(peer_symbol)
        info = t.info or {}
        if not info.get("shortName") and not info.get("longName"):
            return None
        roe = _safe_float(info.get("returnOnEquity"))
        margin = _safe_float(info.get("profitMargins"))
        return {
            "symbol": peer_symbol,
            "name": info.get("shortName") or info.get("longName") or peer_symbol,
            "market_cap": _safe_float(info.get("marketCap")),
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "pb_ratio": _safe_float(info.get("priceToBook")),
            "roe_pct": round(roe * 100, 2) if roe is not None else None,
            "profit_margin_pct": round(margin * 100, 2) if margin is not None else None,
        }
    except Exception:
        return None


def run_fundamental_analysis(symbol: str, market: str = "NASDAQ") -> dict:
    resolved_symbol = _resolve_symbol(symbol, market)
    ticker = yf.Ticker(resolved_symbol)
    info = ticker.info or {}

    if not info or (not info.get("shortName") and not info.get("longName") and not info.get("currentPrice")):
        raise ValueError(f"No fundamental data found for symbol '{resolved_symbol}'.")

    income_stmt = ticker.financials
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow

    data_issues = []

    # 1. Historical Revenue & Earnings Comparison
    rev_by_year = _extract_row_series(income_stmt, ["Total Revenue", "Operating Revenue"])
    net_inc_by_year = _extract_row_series(income_stmt, ["Net Income", "Net Income Common Stockholders"])
    ebitda_by_year = _extract_row_series(income_stmt, ["EBITDA", "Normalized EBITDA"])

    years = sorted(set(rev_by_year.keys()) | set(net_inc_by_year.keys()))
    historical_comparison = []
    for y in years:
        rev = rev_by_year.get(y)
        ni = net_inc_by_year.get(y)
        margin = round((ni / rev) * 100, 2) if (rev and ni is not None and rev != 0) else None
        historical_comparison.append({
            "year": y,
            "revenue": rev,
            "net_income": ni,
            "ebitda": ebitda_by_year.get(y),
            "net_margin_pct": margin,
        })

    if len(historical_comparison) < 2:
        data_issues.append("Fewer than 2 years of historical income statement data available for trend comparison.")

    # Calculate YoY growth from latest 2 available years
    rev_growth_yoy = None
    earnings_growth_yoy = None
    if len(historical_comparison) >= 2:
        latest = historical_comparison[-1]
        prev = historical_comparison[-2]
        rev_growth_yoy = _pct_change(latest["revenue"], prev["revenue"])
        earnings_growth_yoy = _pct_change(latest["net_income"], prev["net_income"])

    # Fallback to yfinance info growth if statement growth missing
    if rev_growth_yoy is None and info.get("revenueGrowth") is not None:
        rev_growth_yoy = round(float(info["revenueGrowth"]) * 100, 2)
    if earnings_growth_yoy is None and info.get("earningsGrowth") is not None:
        earnings_growth_yoy = round(float(info["earningsGrowth"]) * 100, 2)

    # 2. Valuation & Financial Ratios (P/E, P/B, ROE, EPS)
    pe_ratio = _safe_float(info.get("trailingPE"))
    forward_pe = _safe_float(info.get("forwardPE"))
    pb_ratio = _safe_float(info.get("priceToBook"))
    eps = _safe_float(info.get("trailingEps"))

    raw_roe = _safe_float(info.get("returnOnEquity"))
    roe_pct = round(raw_roe * 100, 2) if raw_roe is not None else None

    # Manual ROE fallback if info didn't provide it
    if roe_pct is None and years:
        equity_by_year = _extract_row_series(balance_sheet, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"])
        latest_yr = years[-1]
        ni_latest = net_inc_by_year.get(latest_yr)
        eq_latest = equity_by_year.get(latest_yr)
        if ni_latest is not None and eq_latest and eq_latest != 0:
            roe_pct = round((ni_latest / eq_latest) * 100, 2)
            if eq_latest < 0:
                data_issues.append("Negative shareholders' equity detected; ROE and P/B ratios may be distorted.")

    # 3. Profitability Metrics
    gross_margin = _safe_float(info.get("grossMargins"))
    operating_margin = _safe_float(info.get("operatingMargins"))
    profit_margin = _safe_float(info.get("profitMargins"))
    roa = _safe_float(info.get("returnOnAssets"))

    profitability = {
        "gross_margin_pct": round(gross_margin * 100, 2) if gross_margin is not None else None,
        "operating_margin_pct": round(operating_margin * 100, 2) if operating_margin is not None else None,
        "net_profit_margin_pct": round(profit_margin * 100, 2) if profit_margin is not None else None,
        "roa_pct": round(roa * 100, 2) if roa is not None else None,
        "roe_pct": roe_pct,
    }

    # 4. Debt & Financial Stability
    total_debt = _safe_float(info.get("totalDebt"))
    total_cash = _safe_float(info.get("totalCash"))
    debt_to_equity = _safe_float(info.get("debtToEquity"))
    current_ratio = _safe_float(info.get("currentRatio"))
    quick_ratio = _safe_float(info.get("quickRatio"))
    free_cash_flow = _safe_float(info.get("freeCashflow"))

    # Note: yfinance returns debtToEquity as a percentage (e.g. 150.0 = 1.50x)
    debt_to_equity_ratio = round(debt_to_equity / 100, 2) if debt_to_equity is not None else None

    stability = {
        "total_debt": total_debt,
        "total_cash": total_cash,
        "debt_to_equity": debt_to_equity_ratio,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "free_cash_flow": free_cash_flow,
    }

    # 5. Missing / Inconsistent Data Checks
    required_checks = {
        "P/E Ratio": pe_ratio,
        "P/B Ratio": pb_ratio,
        "ROE": roe_pct,
        "Net Profit Margin": profitability["net_profit_margin_pct"],
        "Debt-to-Equity": debt_to_equity_ratio,
        "Current Ratio": current_ratio,
    }
    for label, value in required_checks.items():
        if value is None:
            data_issues.append(f"Missing metric: {label} is not available from the data source.")

    if pe_ratio is not None and pe_ratio < 0:
        data_issues.append("Negative P/E ratio detected (company reported net losses).")
    if debt_to_equity_ratio is not None and debt_to_equity_ratio > 3.0:
        data_issues.append(f"High leverage warning: Debt-to-Equity is {debt_to_equity_ratio}x.")
    if current_ratio is not None and current_ratio < 1.0:
        data_issues.append(f"Short-term liquidity concern: Current Ratio is below 1.0 ({current_ratio}).")

    # 6. Peer Comparison
    sector = info.get("sector")
    peer_symbols = PEER_MAP.get(resolved_symbol)
    if not peer_symbols and sector in SECTOR_DEFAULT_PEERS:
        peer_symbols = [p for p in SECTOR_DEFAULT_PEERS[sector] if p != resolved_symbol]

    peers = []
    if peer_symbols:
        for p_sym in peer_symbols[:3]:
            snap = _fetch_peer_snapshot(p_sym)
            if snap:
                peers.append(snap)
    if not peers:
        data_issues.append("No comparable peer data could be retrieved for this symbol.")

    # 7. Agent Narrative Summary
    company_name = info.get("longName") or info.get("shortName") or resolved_symbol
    summary_points = []

    if rev_growth_yoy is not None:
        direction = "grew" if rev_growth_yoy >= 0 else "declined"
        summary_points.append(
            f"{company_name}'s revenue {direction} by {abs(rev_growth_yoy)}% year-over-year"
            + (f", while net earnings changed by {earnings_growth_yoy}%." if earnings_growth_yoy is not None else ".")
        )
    else:
        summary_points.append(f"Year-over-year revenue growth for {company_name} could not be determined from available statements.")

    if profitability["net_profit_margin_pct"] is not None:
        margin_desc = "strong" if profitability["net_profit_margin_pct"] >= 15 else ("moderate" if profitability["net_profit_margin_pct"] >= 5 else "thin/negative")
        summary_points.append(
            f"Profitability appears {margin_desc} with a net profit margin of {profitability['net_profit_margin_pct']}%"
            + (f" and ROE of {roe_pct}%." if roe_pct is not None else ".")
        )

    if debt_to_equity_ratio is not None:
        lev_desc = "conservative" if debt_to_equity_ratio < 0.8 else ("moderate" if debt_to_equity_ratio <= 2.0 else "high")
        summary_points.append(
            f"Financial stability reflects {lev_desc} leverage (Debt-to-Equity: {debt_to_equity_ratio}x)"
            + (f" and a Current Ratio of {current_ratio}." if current_ratio is not None else ".")
        )

    if pe_ratio is not None:
        val_desc = "premium" if pe_ratio > 30 else ("reasonable" if pe_ratio >= 12 else "value-oriented")
        summary_points.append(
            f"On valuation, the stock trades at a {val_desc} P/E of {pe_ratio}"
            + (f" and P/B of {pb_ratio}." if pb_ratio is not None else ".")
        )

    return {
        "agent": "Fundamental Analysis Agent",
        "metadata": {
            "resolved_symbol": resolved_symbol,
            "company_name": company_name,
            "sector": sector,
            "industry": info.get("industry"),
            "currency": info.get("currency", "USD"),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
        "revenue_and_earnings": {
            "revenue_growth_yoy_pct": rev_growth_yoy,
            "earnings_growth_yoy_pct": earnings_growth_yoy,
            "trailing_eps": eps,
            "market_cap": _safe_float(info.get("marketCap")),
        },
        "valuation_ratios": {
            "pe_ratio": pe_ratio,
            "forward_pe": forward_pe,
            "pb_ratio": pb_ratio,
            "roe_pct": roe_pct,
        },
        "profitability": profitability,
        "debt_and_stability": stability,
        "historical_comparison": historical_comparison,
        "peer_comparison": peers,
        "data_quality_issues": data_issues,
        "agent_summary": " ".join(summary_points),
    }