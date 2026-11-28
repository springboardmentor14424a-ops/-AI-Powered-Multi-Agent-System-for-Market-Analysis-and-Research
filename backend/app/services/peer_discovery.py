"""
peer_discovery.py
=================
Automatic industry peer discovery service for the Fundamental Agent.

Discovers relevant industry peers dynamically using Yahoo Finance metadata:
  1. Multi-tier discovery strategy:
     - Tier 1: yf.screen(EquityQuery) filtered by geographic region and industry/sector.
     - Tier 2: yf.Industry(industry_key).top_companies.
     - Tier 3: yf.Search fallback with industry/sector keywords.
  2. Zero hardcoded company-to-peer mappings.
  3. Excludes target company and removes duplicate candidates.
  4. Selects top competitors (preferring 3-4 peers, configurable max 5).
  5. Validates relevance and handles network/provider failures gracefully.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
import yfinance as yf

logger = logging.getLogger(__name__)


def normalize_industry_key(industry: Optional[str]) -> Optional[str]:
    """
    Convert display industry name into Yahoo Finance kebab-case key.
    e.g. 'Information Technology Services' -> 'information-technology-services'
    'Oil & Gas Integrated' -> 'oil-gas-integrated'
    """
    if not industry:
        return None
    clean = re.sub(r"[^a-zA-Z0-9\s-]", "", industry.replace("&", " "))
    words = clean.lower().split()
    return "-".join(words) if words else None


def normalize_ticker(ticker: str) -> str:
    """
    Normalize ticker symbol by removing exchange suffixes (.NS, .BO)
    and trimming whitespace.
    """
    if not ticker:
        return ""
    s = str(ticker).strip().upper()
    if s.endswith(".NS"):
        s = s[:-3]
    elif s.endswith(".BO"):
        s = s[:-3]
    return s


def is_same_ticker(tick1: str, tick2: str) -> bool:
    """Check if two tickers represent the same base company."""
    return normalize_ticker(tick1) == normalize_ticker(tick2)


def get_market_region(market: str) -> str:
    """Map market code to yfinance screener region."""
    m = (market or "").strip().upper()
    if m in ("NSE", "BSE"):
        return "in"
    if m in ("NASDAQ", "NYSE", "AMEX"):
        return "us"
    return "in" if m in ("IN", "INDIA") else "us"


def _screen_by_query(query: Any, limit: int = 15) -> List[Dict[str, Any]]:
    """Execute yf.screen with EquityQuery safely, prioritizing top market-cap peers."""
    try:
        if not hasattr(yf, "screen"):
            return []
        try:
            res = yf.screen(query, size=limit, sortField="intradaymarketcap", sortAsc=False)
        except (TypeError, Exception):
            res = yf.screen(query, size=limit)
        quotes = []
        if isinstance(res, dict):
            quotes = res.get("quotes", [])
        elif hasattr(res, "quotes"):
            quotes = getattr(res, "quotes") or []
        elif hasattr(res, "get"):
            quotes = res.get("quotes", [])

        results = []
        for q in quotes:
            sym = q.get("symbol")
            if not sym:
                continue
            results.append({
                "symbol": sym,
                "name": q.get("shortName") or q.get("longName") or sym,
                "market_cap": q.get("marketCap"),
                "source": "screener",
            })
        return results
    except Exception as exc:
        logger.debug("yf.screen query failed: %s", exc)
        return []


def _discover_tier1_screener(
    market: str,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """
    Tier 1 Discovery: Use yf.screen(EquityQuery) with region and sector/industry.
    """
    if not hasattr(yf, "EquityQuery"):
        return []

    region = get_market_region(market)
    candidates: List[Dict[str, Any]] = []

    # Attempt A: Region + Industry (most specific)
    if industry:
        try:
            q_ind = yf.EquityQuery("and", [
                yf.EquityQuery("eq", ["region", region]),
                yf.EquityQuery("eq", ["industry", industry]),
            ])
            candidates = _screen_by_query(q_ind, limit=limit)
        except Exception as exc:
            logger.debug("Tier 1 industry screen failed: %s", exc)

    # Attempt B: Region + Sector if industry gave fewer than 3 candidates
    if len(candidates) < 3 and sector:
        try:
            q_sec = yf.EquityQuery("and", [
                yf.EquityQuery("eq", ["region", region]),
                yf.EquityQuery("eq", ["sector", sector]),
            ])
            sec_candidates = _screen_by_query(q_sec, limit=limit)
            # Merge while avoiding duplicate symbols
            existing_syms = {normalize_ticker(c["symbol"]) for c in candidates}
            for sc in sec_candidates:
                if normalize_ticker(sc["symbol"]) not in existing_syms:
                    candidates.append(sc)
                    existing_syms.add(normalize_ticker(sc["symbol"]))
        except Exception as exc:
            logger.debug("Tier 1 sector screen failed: %s", exc)

    return candidates


def _discover_tier2_industry_hierarchy(
    industry_key: Optional[str],
    market: str,
) -> List[Dict[str, Any]]:
    """
    Tier 2 Discovery: Use yf.Industry(industry_key).top_companies.
    """
    if not industry_key or not hasattr(yf, "Industry"):
        return []

    try:
        ind = yf.Industry(industry_key)
        top = getattr(ind, "top_companies", None)
        if top is None:
            return []

        results: List[Dict[str, Any]] = []
        # top can be a DataFrame or list/dict
        if hasattr(top, "iterrows"):
            for idx, row in top.iterrows():
                row_dict = row.to_dict() if hasattr(row, "to_dict") else {}
                sym = str(idx) if idx else str(row_dict.get("symbol") or "")
                if not sym or sym.lower() == "nan":
                    sym = str(row_dict.get("symbol") or "")
                if sym:
                    results.append({
                        "symbol": sym,
                        "name": str(row_dict.get("name") or row_dict.get("company_name") or sym),
                        "market_cap": row_dict.get("market_cap") or row_dict.get("marketCap"),
                        "source": "industry_hierarchy",
                    })
        elif isinstance(top, (list, tuple)):
            for item in top:
                if isinstance(item, dict):
                    sym = item.get("symbol")
                    if sym:
                        results.append({
                            "symbol": sym,
                            "name": item.get("name") or sym,
                            "market_cap": item.get("market_cap"),
                            "source": "industry_hierarchy",
                        })
                elif isinstance(item, str):
                    results.append({
                        "symbol": item,
                        "name": item,
                        "market_cap": None,
                        "source": "industry_hierarchy",
                    })

        # Match region if market is Indian (.NS/.BO) vs US
        is_indian = get_market_region(market) == "in"
        filtered = []
        for r in results:
            s = r["symbol"].upper()
            if is_indian:
                if s.endswith(".NS") or s.endswith(".BO"):
                    filtered.append(r)
            else:
                if not (s.endswith(".NS") or s.endswith(".BO")):
                    filtered.append(r)

        return filtered if filtered else results
    except Exception as exc:
        logger.debug("Tier 2 industry hierarchy failed: %s", exc)
        return []


def _discover_tier3_search(
    query_str: str,
    market: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tier 3 Fallback: Use yf.Search for keyword discovery.
    """
    if not query_str or not hasattr(yf, "Search"):
        return []

    try:
        search = yf.Search(query_str, max_results=limit)
        quotes = getattr(search, "quotes", []) or []
        results: List[Dict[str, Any]] = []
        is_indian = get_market_region(market) == "in"

        for q in quotes:
            if not isinstance(q, dict):
                continue
            quote_type = (q.get("quoteType") or "").upper()
            if quote_type and quote_type != "EQUITY":
                continue

            sym = q.get("symbol")
            if not sym:
                continue

            s_upper = sym.upper()
            if is_indian and not (s_upper.endswith(".NS") or s_upper.endswith(".BO")):
                continue
            elif not is_indian and (s_upper.endswith(".NS") or s_upper.endswith(".BO")):
                continue

            results.append({
                "symbol": sym,
                "name": q.get("shortname") or q.get("longname") or sym,
                "market_cap": None,
                "source": "search",
            })
        return results
    except Exception as exc:
        logger.debug("Tier 3 search failed: %s", exc)
        return []


def discover_peer_candidates(
    target_ticker: str,
    market: str = "NSE",
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    industry_key: Optional[str] = None,
    max_peers: int = 4,
) -> List[Dict[str, Any]]:
    """
    Discover industry peer candidate companies dynamically.

    Parameters:
      target_ticker:  The ticker of the company being analyzed (excluded from results).
      market:         Target market ('NSE', 'BSE', 'NASDAQ', 'NYSE').
      sector:         Company sector name (e.g. 'Technology', 'Financial Services').
      industry:       Company industry name (e.g. 'Information Technology Services').
      industry_key:   Yahoo Finance industry key (e.g. 'information-technology-services').
      max_peers:      Maximum number of peers to return (capped at 5, default 4).

    Returns:
      List of peer candidate dictionaries containing symbol, name, market_cap, and source.
    """
    clean_target = normalize_ticker(target_ticker)
    cap_limit = max(1, min(max_peers, 5))

    raw_candidates: List[Dict[str, Any]] = []

    # Tier 1: yf.screen(EquityQuery)
    tier1_res = _discover_tier1_screener(market=market, sector=sector, industry=industry, limit=15)
    raw_candidates.extend(tier1_res)

    resolved_ind_key = industry_key or normalize_industry_key(industry)

    # Tier 2: yf.Industry(resolved_ind_key).top_companies if Tier 1 found < 3
    if len(raw_candidates) < 3 and resolved_ind_key:
        tier2_res = _discover_tier2_industry_hierarchy(industry_key=resolved_ind_key, market=market)
        raw_candidates.extend(tier2_res)

    # Tier 3: Keyword search fallback if still < 3
    if len(raw_candidates) < 3:
        query_kw = sector or (industry.split()[0] if industry else "")
        if query_kw:
            tier3_res = _discover_tier3_search(query_kw, market=market, limit=10)
            raw_candidates.extend(tier3_res)

    # Filtering & Deduplication:
    # 1. Exclude the target ticker
    # 2. Deduplicate symbols by normalized ticker
    seen_tickers: Set[str] = {clean_target}
    filtered: List[Dict[str, Any]] = []

    for cand in raw_candidates:
        sym = cand.get("symbol")
        if not sym:
            continue
        norm_sym = normalize_ticker(sym)
        if norm_sym in seen_tickers:
            continue
        seen_tickers.add(norm_sym)
        # Store clean display ticker
        clean_cand = dict(cand)
        clean_cand["clean_ticker"] = norm_sym
        filtered.append(clean_cand)

    # Sort candidates by market_cap descending (largest peers first)
    def _sort_key(c: Dict[str, Any]) -> float:
        mc = c.get("market_cap")
        if mc is not None and isinstance(mc, (int, float)):
            return float(mc)
        return -1.0

    filtered.sort(key=_sort_key, reverse=True)

    return filtered[:cap_limit]


def discover_peer_tickers(
    target_ticker: str,
    market: str = "NSE",
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    industry_key: Optional[str] = None,
    max_peers: int = 4,
) -> List[str]:
    """
    Convenience function returning a list of peer ticker symbols.
    """
    candidates = discover_peer_candidates(
        target_ticker=target_ticker,
        market=market,
        sector=sector,
        industry=industry,
        industry_key=industry_key,
        max_peers=max_peers,
    )
    return [c["clean_ticker"] for c in candidates if c.get("clean_ticker")]
