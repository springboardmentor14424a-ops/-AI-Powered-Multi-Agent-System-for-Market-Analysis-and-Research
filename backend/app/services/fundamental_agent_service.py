"""
fundamental_agent_service.py
=============================
Bridge service connecting the data retrieval layer (company_data) with
the Fundamental Agent analytical engine (backend/ml/financial_agent/core).

Capabilities:
  1. Dynamically accepts any ticker and market (NSE, BSE, NASDAQ, NYSE).
  2. Reuses existing company_data service for yfinance profile & statements.
  3. Formats and normalizes statement data into pandas DataFrames for core.py.
  4. Runs all available Fundamental Agent features in-memory (Features 1–5, 7, 8, and optional 6).
  5. Enforces strict JSON safety (allow_nan=False): converts NaN/Inf to null,
     normalizes numpy/pandas scalars to native Python types.
  6. Returns structured dictionaries ready for FastAPI endpoints and orchestrator agents.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

try:
    from app.services.company_data import (
        get_company_profile,
        get_financial_statements,
    )
    from app.services.peer_discovery import (
        discover_peer_candidates,
        normalize_ticker,
    )
except ImportError:
    from backend.app.services.company_data import (
        get_company_profile,
        get_financial_statements,
    )
    from backend.app.services.peer_discovery import (
        discover_peer_candidates,
        normalize_ticker,
    )

try:
    from ml.financial_agent.core import (
        run_fundamental_analysis,
        analyze_revenue_earnings,
        analyze_profitability,
        analyze_debt_stability,
        analyze_financial_ratios,
    )
except ImportError:
    from backend.ml.financial_agent.core import (
        run_fundamental_analysis,
        analyze_revenue_earnings,
        analyze_profitability,
        analyze_debt_stability,
        analyze_financial_ratios,
    )


# ---------------------------------------------------------------------------
# STRICT JSON SANITIZER
# ---------------------------------------------------------------------------

def sanitize_for_strict_json(obj: Any) -> Any:
    """
    Recursively sanitize data structures for strict JSON serialization.

    Guarantees:
      - All float('nan'), float('inf'), and float('-inf') are converted to None (JSON null).
      - NumPy scalars (np.int64, np.float64, np.bool_) are converted to native Python types.
      - Pandas Timestamps / datetimes are converted to ISO format strings.
      - Compatible with json.dumps(result, allow_nan=False).
    """
    if obj is None:
        return None

    # Handle float NaN / Inf
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        if math.isnan(f) or math.isinf(f):
            return None
        return f

    # Handle booleans first (since bool is a subclass of int in Python)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)

    # Handle integers
    if isinstance(obj, (int, np.integer)):
        return int(obj)

    # Handle datetimes & timestamps
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    if isinstance(obj, np.datetime64):
        return str(obj)

    # Handle dictionaries
    if isinstance(obj, dict):
        return {str(k): sanitize_for_strict_json(v) for k, v in obj.items()}

    # Handle lists, tuples, sets
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_strict_json(item) for item in obj]

    # Handle pandas DataFrame / Series if encountered directly
    if isinstance(obj, pd.DataFrame):
        records = obj.to_dict(orient="records")
        return [sanitize_for_strict_json(r) for r in records]
    if isinstance(obj, pd.Series):
        return sanitize_for_strict_json(obj.to_dict())

    return obj


# ---------------------------------------------------------------------------
# DATA NORMALIZATION HELPERS
# ---------------------------------------------------------------------------

def _dict_statement_to_dataframe(statement_data: Optional[Dict[str, Dict[str, Any]]]) -> pd.DataFrame:
    """
    Convert the serialized dictionary returned by company_data.get_financial_statements
    into the statement DataFrame layout expected by core.py.

    Input shape from company_data:
      {"2026-03-31": {"Total Revenue": 1000.0, "Net Income": 100.0}, ...}

    Output DataFrame shape for core.py:
      Index = Line Item names ("Total Revenue", "Net Income")
      Columns = Period Date strings ("2026-03-31", "2025-03-31")
    """
    if not statement_data or not isinstance(statement_data, dict):
        return pd.DataFrame()

    try:
        df = pd.DataFrame(statement_data)
        return df
    except Exception:
        return pd.DataFrame()


def _fetch_peer_metrics(
    peer_ticker: str,
    market: str,
    target_currency: str,
) -> Optional[Dict[str, Any]]:
    """
    Safely retrieve profile and statements for a peer, computing its latest standard
    comparative metrics via the core analytical functions.

    Returns None on failure without raising exceptions or breaking callers.
    """
    try:
        clean_peer = normalize_ticker(peer_ticker)
        prof_res = get_company_profile(clean_peer, market)
        if not prof_res or not prof_res.get("success"):
            return None
        prof = prof_res.get("profile") or {}

        inc_res = get_financial_statements(clean_peer, market, statement="income", frequency="annual")
        if not inc_res or not inc_res.get("success") or not inc_res.get("data"):
            return None

        bs_res = get_financial_statements(clean_peer, market, statement="balance_sheet", frequency="annual")

        inc_df = _dict_statement_to_dataframe(inc_res.get("data"))
        bs_df = _dict_statement_to_dataframe(bs_res.get("data")) if (bs_res and bs_res.get("success")) else pd.DataFrame()

        if inc_df.empty:
            return None

        # Re-use core analytical calculations for 100% calculation parity
        rev_df = analyze_revenue_earnings(inc_df)
        prof_df = analyze_profitability(inc_df)
        debt_df = analyze_debt_stability(bs_df)
        rat_df = analyze_financial_ratios(inc_df, bs_df, market_price=prof.get("current_price"))

        latest_rev = rev_df.iloc[-1].to_dict() if not rev_df.empty else {}
        latest_prof = prof_df.iloc[-1].to_dict() if not prof_df.empty else {}
        latest_debt = debt_df.iloc[-1].to_dict() if not debt_df.empty else {}
        latest_rat = rat_df.iloc[-1].to_dict() if not rat_df.empty else {}

        peer_curr = prof.get("currency") or target_currency
        sector_name = prof.get("sector")
        industry_name = prof.get("industry")

        return {
            "Ticker":                 clean_peer,
            "Company_Name":           prof.get("company_name") or clean_peer,
            "Currency":               peer_curr,
            "Sector":                 sector_name,
            "Industry":               industry_name,
            "FY_Period":              latest_rev.get("Financial_Year", "Latest"),
            "Revenue":                latest_rev.get("Revenue"),
            "Revenue_Growth_%":       latest_rev.get("Revenue_Growth_%"),
            "Net_Income":             latest_rev.get("Net_Income"),
            "Net_Income_Growth_%":    latest_rev.get("Earnings_Growth_%"),
            "Gross_Profit_Margin_%":  latest_prof.get("Gross_Profit_Margin_%"),
            "Operating_Margin_%":     latest_prof.get("Operating_Margin_%"),
            "Net_Profit_Margin_%":    latest_prof.get("Net_Profit_Margin_%"),
            "EBITDA_Margin_%":        latest_prof.get("EBITDA_Margin_%"),
            "Debt_to_Equity":         latest_debt.get("Debt_to_Equity_Ratio"),
            "Debt_to_Assets":         latest_debt.get("Debt_to_Assets_Ratio"),
            "Current_Ratio":          latest_debt.get("Current_Ratio"),
            "ROE_%":                  latest_rat.get("ROE_%"),
            "EPS":                    latest_rat.get("EPS"),
            "PE_Ratio":               latest_rat.get("PE_Ratio") or prof.get("pe_ratio"),
            "PB_Ratio":               latest_rat.get("PB_Ratio") or prof.get("pb_ratio"),
            "Peer_Rationale":         f"Discovered {industry_name or sector_name or 'industry'} peer ({market})",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# MAIN SERVICE API
# ---------------------------------------------------------------------------

def analyze_company_fundamentals(
    ticker: str,
    market: str = "NSE",
    peer_companies: Optional[Union[List[Dict[str, Any]], pd.DataFrame]] = None,
    custom_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Dynamically retrieve financial statements for a requested company and execute
    the Fundamental Agent analytical engine.

    Parameters:
      ticker:             Stock ticker symbol (e.g. 'TCS', 'RELIANCE', 'AAPL', 'MSFT').
      market:             Exchange identifier ('NSE', 'BSE', 'NASDAQ', 'NYSE').
      peer_companies:     Optional list/DataFrame of peer financial metrics for Feature 6.
      custom_thresholds:  Optional dict of custom profitability tier thresholds.

    Returns:
      Strict JSON-safe dictionary containing complete Fundamental Agent results or error details.
    """
    clean_ticker = (ticker or "").strip().upper()
    clean_market = (market or "NSE").strip().upper()

    if not clean_ticker:
        return sanitize_for_strict_json({
            "success": False,
            "error": "Ticker symbol must be provided.",
            "ticker": clean_ticker,
            "market": clean_market,
            "agent_name": "Fundamental Agent",
        })

    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Retrieve Company Profile (identity, currency, sector, latest price)
    try:
        profile_res = get_company_profile(clean_ticker, clean_market)
    except Exception as exc:
        return sanitize_for_strict_json({
            "success": False,
            "error": f"Failed to retrieve company profile: {exc}",
            "ticker": clean_ticker,
            "market": clean_market,
            "agent_name": "Fundamental Agent",
        })

    if not profile_res or not profile_res.get("success") or not profile_res.get("profile"):
        err_msg = profile_res.get("message") if profile_res else "Company profile not found"
        return sanitize_for_strict_json({
            "success": False,
            "error": f"Company profile retrieval failed: {err_msg}",
            "ticker": clean_ticker,
            "market": clean_market,
            "agent_name": "Fundamental Agent",
        })

    profile = profile_res["profile"]
    company_name = profile.get("company_name") or clean_ticker
    currency     = profile.get("currency") or ("USD" if clean_market in ("NASDAQ", "NYSE") else "INR")
    sector       = profile.get("sector")
    industry     = profile.get("industry")
    market_price = profile.get("current_price")
    data_source  = profile_res.get("data_source") or "Yahoo Finance (via company_data service)"

    # 2. Retrieve Financial Statements via company_data service
    try:
        inc_res = get_financial_statements(clean_ticker, clean_market, statement="income", frequency="annual")
        bs_res  = get_financial_statements(clean_ticker, clean_market, statement="balance_sheet", frequency="annual")
    except Exception as exc:
        return sanitize_for_strict_json({
            "success": False,
            "error": f"Failed to retrieve financial statements: {exc}",
            "ticker": clean_ticker,
            "market": clean_market,
            "company_name": company_name,
            "agent_name": "Fundamental Agent",
        })

    # Validate that at least income statement is available
    if not inc_res or not inc_res.get("success") or not inc_res.get("data"):
        err_msg = inc_res.get("message") if inc_res else "Income statement data unavailable"
        return sanitize_for_strict_json({
            "success": False,
            "error": f"Annual income statement could not be retrieved: {err_msg}",
            "ticker": clean_ticker,
            "market": clean_market,
            "company_name": company_name,
            "agent_name": "Fundamental Agent",
        })

    # 3. Normalize statement data into DataFrames for core.py
    income_stmt_df   = _dict_statement_to_dataframe(inc_res.get("data"))
    balance_sheet_df = _dict_statement_to_dataframe(bs_res.get("data")) if (bs_res and bs_res.get("success")) else pd.DataFrame()

    warnings: List[str] = []
    if balance_sheet_df.empty:
        warnings.append("Annual balance sheet was unavailable; balance sheet and leverage ratios will be omitted.")

    # 4. Handle Peer Companies: Use supplied peers or dynamically auto-discover
    active_peers = peer_companies
    peer_discovery_status = None
    peer_discovery_warnings: List[str] = []

    if active_peers is None:
        try:
            industry_key = None
            if isinstance(profile.get("info"), dict):
                industry_key = profile["info"].get("industryKey")

            discovered_candidates = discover_peer_candidates(
                target_ticker=clean_ticker,
                market=clean_market,
                sector=sector,
                industry=industry,
                industry_key=industry_key,
                max_peers=4,
            )

            discovered_metrics: List[Dict[str, Any]] = []
            for cand in discovered_candidates:
                cand_sym = cand.get("clean_ticker") or cand.get("symbol")
                if not cand_sym:
                    continue
                p_metrics = _fetch_peer_metrics(
                    peer_ticker=cand_sym,
                    market=clean_market,
                    target_currency=currency,
                )
                if p_metrics:
                    discovered_metrics.append(p_metrics)

            if discovered_metrics:
                active_peers = discovered_metrics
                peer_discovery_status = "auto_discovered"
            else:
                peer_discovery_status = "no_peers_found"
                peer_discovery_warnings.append(
                    f"Automatic peer discovery could not find sufficient peers with available financial data for {clean_ticker}."
                )
        except Exception as exc:
            peer_discovery_status = "discovery_failed"
            peer_discovery_warnings.append(f"Automatic peer discovery encountered an error: {exc}")

    # 5. Execute Fundamental Agent Core Engine
    try:
        raw_analysis = run_fundamental_analysis(
            income_stmt=income_stmt_df,
            balance_sheet=balance_sheet_df,
            market_price=market_price,
            price_date=retrieval_timestamp.split("T")[0],
            currency=currency,
            ticker=clean_ticker,
            thresholds=custom_thresholds,
            peer_companies=active_peers,
        )
    except Exception as exc:
        return sanitize_for_strict_json({
            "success": False,
            "error": f"Analytical core calculation error: {exc}",
            "ticker": clean_ticker,
            "market": clean_market,
            "company_name": company_name,
            "agent_name": "Fundamental Agent",
        })

    # Ensure Feature 6 has a structured informative payload even if peers are unavailable
    if raw_analysis.get("peer_comparison") is None:
        raw_analysis["peer_comparison"] = {
            "status": "unavailable",
            "message": "Peer comparison unavailable: automatic discovery could not find sufficient peers with available data.",
            "target_ticker": clean_ticker,
            "target_company_name": company_name,
            "target_currency": currency,
            "companies_compared": 1,
            "peer_count": 0,
            "companies": [],
            "comparison_table": [],
            "peer_benchmarks": {},
            "warnings": peer_discovery_warnings,
        }
    else:
        if peer_discovery_status:
            raw_analysis["peer_comparison"]["discovery_status"] = peer_discovery_status
        if peer_discovery_warnings:
            raw_analysis["peer_comparison"].setdefault("warnings", []).extend(peer_discovery_warnings)

    # Combine service-level warnings with data quality warnings
    if warnings and "data_quality" in raw_analysis and isinstance(raw_analysis["data_quality"], dict):
        for w in warnings:
            raw_analysis["data_quality"].setdefault("issues", []).append({
                "Ticker": clean_ticker,
                "Category": "Missing Data",
                "Severity": "WARNING",
                "Source_File": "company_data service",
                "Metric": "Balance_Sheet",
                "Period": "All",
                "Description": w,
                "Impact": "Leverage and stability analysis omitted",
            })

    # 5. Build Final Response Envelope
    response = {
        "success":               True,
        "agent_name":            "Fundamental Agent",
        "ticker":                clean_ticker,
        "market":                clean_market,
        "company_name":          company_name,
        "currency":              currency,
        "sector":                sector,
        "industry":              industry,
        "market_price":          market_price,
        "retrieved_at":          retrieval_timestamp,
        "data_source":           data_source,
        "reporting_periods":     inc_res.get("reporting_periods", []),
        "analysis":              raw_analysis,
    }

    # 6. Apply Strict JSON Sanitization (converts NaN to null, native types)
    return sanitize_for_strict_json(response)
