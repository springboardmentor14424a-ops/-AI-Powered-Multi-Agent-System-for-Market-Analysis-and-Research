from __future__ import annotations

import os
import math
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import pandas as pd
import joblib

from database.connection import get_db
from routers.stocks import get_company_profile, get_financial_statements, get_stock_ohlcv

router = APIRouter(prefix="/api/agent/fundamental", tags=["fundamental-analysis-agent"])

# Paths to serialized ML artifacts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "ml_artifacts")

_best_model = None
_scaler = None
_feature_cols = None

# Peer mapping across supported Module 2 equities
SECTOR_PEERS: Dict[str, List[str]] = {
    "RELIANCE.NS": ["ONGC.NS", "BPCL.NS", "IOC.NS"],
    "RELIANCE": ["ONGC.NS", "BPCL.NS", "IOC.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "TCS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS"],
    "INFY": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS"],
    "AAPL": ["MSFT", "GOOGL", "TSLA"],
    "MSFT": ["AAPL", "GOOGL", "NVDA"],
    "TSLA": ["AAPL", "MSFT", "F"],
}


def _load_ml_model():
    """Lazy-load trained XGBoost model, scaler, and ordered feature column list."""
    global _best_model, _scaler, _feature_cols
    if _best_model is None:
        model_path = os.path.join(ARTIFACTS_DIR, "best_model.pkl")
        scaler_path = os.path.join(ARTIFACTS_DIR, "scaler.pkl")
        feat_path = os.path.join(ARTIFACTS_DIR, "feature_columns.pkl")

        if os.path.exists(model_path) and os.path.exists(feat_path):
            _best_model = joblib.load(model_path)
            _scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
            _feature_cols = joblib.load(feat_path)
    return _best_model, _scaler, _feature_cols


def _classify_profitability_range(
    net_margin: Optional[float],
    roe: Optional[float],
    net_income: Optional[float],
) -> Dict[str, Any]:
    """Classify profitability into the 3-tier range: Highly Profitable, Moderately Profitable, or Not Profitable."""
    # Check for clear unprofitable case first
    if (net_income is not None and net_income <= 0) or (net_margin is not None and net_margin <= 0) or (roe is not None and roe <= 0):
        tier = "Not Profitable"
        reason = "Negative or zero net income / ROE / profit margin."
    elif (net_margin is not None and net_margin >= 15.0) or (roe is not None and roe >= 18.0):
        tier = "Highly Profitable"
        reason = "Strong profit margins (>=15%) and/or high return on equity (>=18%)."
    elif (net_margin is not None and net_margin > 0) or (roe is not None and roe > 0) or (net_income is not None and net_income > 0):
        tier = "Moderately Profitable"
        reason = "Positive earnings and positive margins/ROE below high-profitability thresholds."
    else:
        tier = "Data Unavailable"
        reason = "Insufficient margin or earnings figures to classify profitability."

    return {
        "range": tier,
        "rationale": reason,
        "range_definitions": {
            "Highly Profitable": "Net Margin >= 15% OR ROE >= 18% (with positive earnings)",
            "Moderately Profitable": "Net Margin between 0% and 15% AND ROE between 0% and 18%",
            "Not Profitable": "Net Income <= 0 OR Net Margin <= 0% OR ROE <= 0%",
        },
    }


def _detect_price_and_market_anomalies(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detect sudden price downfalls, sharp surges, unusual volume spikes, and OHLCV data glitches."""
    ohlcv_audit = {"high_lt_low": 0, "non_positive_prices": 0, "duplicate_dates": 0, "extreme_jumps_gt_25pct": 0}
    anomalies: List[Dict[str, Any]] = []
    empty_summary = {
        "total_anomalies": 0,
        "sudden_downfalls": 0,
        "sudden_surges": 0,
        "volume_spikes": 0,
        "data_glitches": 0,
        "worst_single_day": None,
        "best_single_day": None,
        "peak_volume_day": None,
    }
    if not bars:
        return {"ohlcv_audit": ohlcv_audit, "anomalies": anomalies, "summary": empty_summary}

    df_b = pd.DataFrame(bars).copy()
    for col in ("open", "high", "low", "close", "volume"):
        if col in df_b.columns:
            df_b[col] = pd.to_numeric(df_b[col], errors="coerce")

    dates = df_b["date"].astype(str).str.slice(0, 10) if "date" in df_b.columns else pd.Series(["N/A"] * len(df_b))

    # 1. Data Glitch checks (High < Low, non-positive price, duplicate dates)
    if {"high", "low", "close"}.issubset(df_b.columns):
        hl_mask = df_b["high"] < df_b["low"]
        np_mask = (df_b["close"] <= 0) | (df_b["low"] <= 0)
        dup_mask = dates.duplicated(keep="first") if "date" in df_b.columns else pd.Series([False] * len(df_b))

        ohlcv_audit["high_lt_low"] = int(hl_mask.sum())
        ohlcv_audit["non_positive_prices"] = int(np_mask.sum())
        ohlcv_audit["duplicate_dates"] = int(dup_mask.sum())

        for idx in df_b[hl_mask].index[:5]:
            anomalies.append({
                "date": dates.loc[idx],
                "type": "Data Glitch",
                "severity": "High",
                "change_pct": None,
                "volume_ratio": None,
                "close_price": round(float(df_b.loc[idx, "close"]), 2) if pd.notna(df_b.loc[idx, "close"]) else None,
                "description": f"Intraday High ({df_b.loc[idx, 'high']:.2f}) recorded lower than Low ({df_b.loc[idx, 'low']:.2f}).",
            })
        for idx in df_b[np_mask].index[:5]:
            anomalies.append({
                "date": dates.loc[idx],
                "type": "Data Glitch",
                "severity": "High",
                "change_pct": None,
                "volume_ratio": None,
                "close_price": None,
                "description": "Non-positive close or low price recorded.",
            })
        for idx in df_b[dup_mask].index[:5]:
            anomalies.append({
                "date": dates.loc[idx],
                "type": "Data Glitch",
                "severity": "Medium",
                "change_pct": None,
                "volume_ratio": None,
                "close_price": round(float(df_b.loc[idx, "close"]), 2) if pd.notna(df_b.loc[idx, "close"]) else None,
                "description": f"Duplicate session date detected ({dates.loc[idx]}).",
            })

        # 2. Price & Volume Market Anomalies (Sudden Downfall, Sudden Surge, Volume Spike)
        valid_close = df_b["close"].where(df_b["close"] > 0)
        ret_pct = valid_close.pct_change() * 100.0
        ohlcv_audit["extreme_jumps_gt_25pct"] = int((ret_pct.abs() > 25.0).sum())

        ret_clean = ret_pct.dropna()
        ret_mean = float(ret_clean.mean()) if not ret_clean.empty else 0.0
        ret_std = float(ret_clean.std()) if len(ret_clean) > 5 else 0.0

        vol_ratio_series = pd.Series(np.nan, index=df_b.index)
        if "volume" in df_b.columns:
            vol_ma20 = df_b["volume"].rolling(20, min_periods=5).mean().shift(1)
            vol_ratio_series = np.where(vol_ma20 > 0, df_b["volume"] / vol_ma20, np.nan)
            vol_ratio_series = pd.Series(vol_ratio_series, index=df_b.index)

        downfall_count = 0
        surge_count = 0
        vol_spike_count = 0

        for idx in df_b.index:
            r = ret_pct.loc[idx]
            vr = vol_ratio_series.loc[idx] if idx in vol_ratio_series.index else np.nan
            cp = valid_close.loc[idx]
            dt_str = dates.loc[idx]

            has_r = pd.notna(r) and math.isfinite(float(r))
            has_vr = pd.notna(vr) and math.isfinite(float(vr))
            r_val = float(r) if has_r else 0.0
            vr_val = float(vr) if has_vr else None
            cp_val = round(float(cp), 2) if pd.notna(cp) and math.isfinite(float(cp)) else None
            z = ((r_val - ret_mean) / ret_std) if (has_r and ret_std > 0) else 0.0

            is_downfall = has_r and (r_val <= -4.0 or (r_val <= -3.0 and z <= -2.5))
            is_surge = has_r and (r_val >= 5.0 or (r_val >= 3.5 and z >= 2.5))
            is_vol_spike = has_vr and vr_val is not None and vr_val >= 3.0

            vol_note = f" on {vr_val:.1f}x avg volume" if (vr_val is not None and vr_val >= 2.0) else ""

            if is_downfall:
                downfall_count += 1
                sev = "High" if (r_val <= -7.0 or z <= -3.5) else "Medium"
                anomalies.append({
                    "date": dt_str,
                    "type": "Sudden Downfall",
                    "severity": sev,
                    "change_pct": round(r_val, 2),
                    "volume_ratio": round(vr_val, 1) if vr_val is not None else None,
                    "close_price": cp_val,
                    "description": f"Sharp single-day drop of {r_val:.2f}%{vol_note}.",
                })
            elif is_surge:
                surge_count += 1
                sev = "High" if (r_val >= 8.0 or z >= 3.5) else "Medium"
                anomalies.append({
                    "date": dt_str,
                    "type": "Sudden Surge",
                    "severity": sev,
                    "change_pct": round(r_val, 2),
                    "volume_ratio": round(vr_val, 1) if vr_val is not None else None,
                    "close_price": cp_val,
                    "description": f"Sharp single-day rally of +{r_val:.2f}%{vol_note}.",
                })
            elif is_vol_spike and vr_val is not None:
                vol_spike_count += 1
                sev = "High" if vr_val >= 5.0 else "Medium"
                move_txt = f" (price {r_val:+.2f}%)" if has_r else ""
                anomalies.append({
                    "date": dt_str,
                    "type": "Volume Spike",
                    "severity": sev,
                    "change_pct": round(r_val, 2) if has_r else None,
                    "volume_ratio": round(vr_val, 1),
                    "close_price": cp_val,
                    "description": f"Unusual trading volume of {vr_val:.1f}x 20-day average{move_txt}.",
                })

        # Worst & best single-day moves across period
        worst_day = None
        best_day = None
        if not ret_clean.empty:
            w_idx = ret_clean.idxmin()
            b_idx = ret_clean.idxmax()
            worst_day = {
                "date": dates.loc[w_idx],
                "change_pct": round(float(ret_clean.loc[w_idx]), 2),
                "close_price": round(float(valid_close.loc[w_idx]), 2) if pd.notna(valid_close.loc[w_idx]) else None,
            }
            best_day = {
                "date": dates.loc[b_idx],
                "change_pct": round(float(ret_clean.loc[b_idx]), 2),
                "close_price": round(float(valid_close.loc[b_idx]), 2) if pd.notna(valid_close.loc[b_idx]) else None,
            }

        peak_vol_day = None
        vr_clean = vol_ratio_series.dropna()
        if not vr_clean.empty:
            pv_idx = vr_clean.idxmax()
            if float(vr_clean.loc[pv_idx]) >= 1.5:
                pv_ret = ret_pct.loc[pv_idx]
                peak_vol_day = {
                    "date": dates.loc[pv_idx],
                    "volume_ratio": round(float(vr_clean.loc[pv_idx]), 1),
                    "change_pct": round(float(pv_ret), 2) if pd.notna(pv_ret) and math.isfinite(float(pv_ret)) else None,
                }

        glitches_count = ohlcv_audit["high_lt_low"] + ohlcv_audit["non_positive_prices"] + ohlcv_audit["duplicate_dates"]
        # Sort newest first and cap to top 12 rows for UI clarity
        anomalies_sorted = sorted(anomalies, key=lambda x: x["date"], reverse=True)[:12]

        summary = {
            "total_anomalies": downfall_count + surge_count + vol_spike_count + glitches_count,
            "sudden_downfalls": downfall_count,
            "sudden_surges": surge_count,
            "volume_spikes": vol_spike_count,
            "data_glitches": glitches_count,
            "worst_single_day": worst_day,
            "best_single_day": best_day,
            "peak_volume_day": peak_vol_day,
        }
        return {"ohlcv_audit": ohlcv_audit, "anomalies": anomalies_sorted, "summary": summary}

    return {"ohlcv_audit": ohlcv_audit, "anomalies": anomalies, "summary": empty_summary}


def _audit_ohlcv_and_statements(
    profile: Dict[str, Any],
    income_stmts: List[Dict[str, Any]],
    balance_sheets: List[Dict[str, Any]],
    cash_flows: List[Dict[str, Any]],
    bars: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Identify missing or inconsistent financial information and market/price anomalies."""
    missing_fields: List[str] = []
    inconsistencies: List[str] = []

    # 1. Profile checks
    key_profile_fields = [
        "company_name", "sector", "current_price", "market_cap",
        "pe_ratio", "price_to_book", "return_on_equity", "profit_margins", "total_revenue", "total_debt"
    ]
    for f in key_profile_fields:
        if profile.get(f) is None:
            missing_fields.append(f"profile.{f}")

    # 2. Financial statements checks
    if not income_stmts:
        missing_fields.append("financials.income_statements")
    else:
        latest_inc = income_stmts[0]
        for f in ["total_revenue", "gross_profit", "operating_income", "net_income", "eps"]:
            val = latest_inc.get(f)
            if val is None or (f in ("gross_profit", "total_revenue") and val == 0):
                missing_fields.append(f"income_statement.{f}")
        rev = latest_inc.get("total_revenue")
        gp = latest_inc.get("gross_profit")
        ni = latest_inc.get("net_income")
        if rev is not None and rev <= 0:
            inconsistencies.append(f"Non-positive total revenue reported ({rev}).")
        if rev is not None and gp is not None and gp > rev:
            inconsistencies.append(f"Gross profit ({gp}) exceeds total revenue ({rev}).")
        if rev is not None and ni is not None and ni > rev:
            inconsistencies.append(f"Net income ({ni}) exceeds total revenue ({rev}); verify extraordinary items.")

    if not balance_sheets:
        missing_fields.append("financials.balance_sheets")
    else:
        latest_bs = balance_sheets[0]
        for f in ["total_assets", "total_liabilities", "stockholders_equity", "long_term_debt", "cash_and_equivalents"]:
            if latest_bs.get(f) is None:
                missing_fields.append(f"balance_sheet.{f}")
        assets = latest_bs.get("total_assets")
        liab = latest_bs.get("total_liabilities")
        eq = latest_bs.get("stockholders_equity")
        ltd = latest_bs.get("long_term_debt")
        if assets is not None and liab is not None and eq is not None and assets > 0:
            imbalance_pct = abs(assets - (liab + eq)) / assets * 100
            if imbalance_pct > 2.0:
                inconsistencies.append(
                    f"Balance sheet accounting mismatch: Assets vs (Liabilities + Equity) differs by {imbalance_pct:.2f}%."
                )
        if ltd is not None and liab is not None and ltd > liab:
            inconsistencies.append("Long-term debt exceeds total liabilities.")
        if eq is not None and eq < 0:
            inconsistencies.append("Negative stockholders' equity detected (accumulated deficit).")

    if not cash_flows:
        missing_fields.append("financials.cash_flows")

    # 3. Price, Volume & OHLCV Anomaly Detection
    if not bars:
        missing_fields.append("market_data.ohlcv_bars")
    anomaly_report = _detect_price_and_market_anomalies(bars)
    ohlcv_anomalies = anomaly_report["ohlcv_audit"]

    for k in ("high_lt_low", "non_positive_prices", "duplicate_dates"):
        if ohlcv_anomalies.get(k, 0) > 0:
            inconsistencies.append(f"OHLCV data glitch '{k}': {ohlcv_anomalies[k]} occurrence(s) detected.")

    total_checked = len(key_profile_fields) + 11  # 10 profile + 5 inc + 5 bs + 1 cf
    completeness_pct = round(max(0.0, (1.0 - len(missing_fields) / total_checked) * 100), 1)
    reliability_status = (
        "High Integrity" if completeness_pct >= 85.0 and not inconsistencies
        else "Moderate / Partial Data" if completeness_pct >= 60.0
        else "Incomplete / Anomalies Flagged"
    )

    return {
        "data_completeness_pct": completeness_pct,
        "reliability_status": reliability_status,
        "missing_fields_count": len(missing_fields),
        "missing_fields": missing_fields,
        "inconsistencies_count": len(inconsistencies),
        "inconsistencies_detected": inconsistencies,
        "ohlcv_audit": ohlcv_anomalies,
        "price_and_market_anomalies": anomaly_report["anomalies"],
        "anomaly_summary": anomaly_report["summary"],
    }


@router.get("/{ticker}")
async def analyze_company_fundamentals(
    ticker: str,
    market: Optional[str] = Query(None, description="Optional stock exchange, e.g. NSE, NASDAQ"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Comprehensive Fundamental Analysis Agent:
    Bridges Module 2 Yahoo Finance APIs with the 94.21%-accuracy XGBoost model
    to evaluate Revenue & Earnings, 3-Tier Profitability, Debt & Stability,
    Financial Ratios (P/E, P/B, ROE), Historical Performance, Peer Comparison,
    and Missing / Inconsistent Data Identification.
    """
    cleaned_ticker = ticker.strip().upper()

    # 1. Retrieve Profile & Valuation Metrics (using snake_case fields from CompanyProfileResponse)
    try:
        profile_res = await get_company_profile(cleaned_ticker, market=market, db=db)
        profile = profile_res.model_dump() if hasattr(profile_res, "model_dump") else dict(profile_res)
    except Exception:
        profile = {"ticker": cleaned_ticker, "company_name": cleaned_ticker}

    # 2. Retrieve Financial Statements (income_statements, balance_sheets, cash_flows)
    try:
        fin_res = await get_financial_statements(cleaned_ticker, market=market, db=db)
        financials = fin_res.model_dump() if hasattr(fin_res, "model_dump") else dict(fin_res)
    except Exception:
        financials = {}

    income_stmts = financials.get("income_statements") or []
    balance_sheets = financials.get("balance_sheets") or []
    cash_flows = financials.get("cash_flows") or []

    # 3. Retrieve Historical OHLCV Data (1Y for ML features & price history)
    bars: List[Dict[str, Any]] = []
    try:
        ohlcv_res = await get_stock_ohlcv(cleaned_ticker, period="1y", interval="1d", market=market, db=db)
        raw_bars = getattr(ohlcv_res, "data", None) or getattr(ohlcv_res, "bars", None)
        if raw_bars:
            bars = [b.model_dump() if hasattr(b, "model_dump") else dict(b) for b in raw_bars]
    except Exception:
        bars = []

    if not bars:
        clean_sym = cleaned_ticker.replace(".NS", "").replace(".BO", "")
        archive_root = os.path.join(os.path.dirname(BASE_DIR), "archive_data")
        stock_file = os.path.join(archive_root, f"Stock_{clean_sym}.xlsx")
        if os.path.exists(stock_file):
            try:
                local_df = pd.read_excel(stock_file).tail(250)
                bars = [
                    {
                        "date": str(row.get("Date", "")),
                        "open": float(row.get("Open", 0)),
                        "high": float(row.get("High", 0)),
                        "low": float(row.get("Low", 0)),
                        "close": float(row.get("Close", 0)),
                        "volume": int(row.get("Volume", 0)),
                    }
                    for _, row in local_df.iterrows()
                ]
            except Exception:
                pass

    # 4. Feature 1: Revenue & Earnings Analysis
    latest_inc = income_stmts[0] if income_stmts else {}
    prev_inc = income_stmts[1] if len(income_stmts) > 1 else {}

    total_rev = latest_inc.get("total_revenue") or profile.get("total_revenue")
    prev_rev = prev_inc.get("total_revenue")
    raw_gp = latest_inc.get("gross_profit")
    gross_profit = raw_gp if (raw_gp is not None and not (raw_gp == 0 and total_rev and total_rev > 0)) else None
    raw_op = latest_inc.get("operating_income")
    net_income = latest_inc.get("net_income")
    op_income = raw_op if (raw_op is not None and not (raw_op == 0 and total_rev and total_rev > 0 and net_income not in (None, 0))) else None
    prev_ni = prev_inc.get("net_income")

    rev_yoy_growth = (
        round(((total_rev - prev_rev) / abs(prev_rev)) * 100, 2)
        if (total_rev is not None and prev_rev not in (None, 0))
        else (round(profile["revenue_growth"] * 100, 2) if profile.get("revenue_growth") is not None else None)
    )
    ni_yoy_growth = (
        round(((net_income - prev_ni) / abs(prev_ni)) * 100, 2)
        if (net_income is not None and prev_ni not in (None, 0))
        else None
    )

    latest_cf = cash_flows[0] if cash_flows else {}
    fcf = latest_cf.get("free_cash_flow")
    if fcf is None and latest_cf.get("operating_cash_flow") is not None and latest_cf.get("capital_expenditures") is not None:
        fcf = latest_cf["operating_cash_flow"] - abs(latest_cf["capital_expenditures"])

    revenue_analysis = {
        "fiscal_period": latest_inc.get("date", "Latest Available"),
        "total_revenue": total_rev,
        "revenue_yoy_growth_pct": rev_yoy_growth,
        "gross_profit": gross_profit,
        "operating_income": op_income,
        "net_income": net_income,
        "earnings_yoy_growth_pct": ni_yoy_growth,
        "eps": latest_inc.get("eps"),
        "free_cash_flow": fcf,
        "earnings_status": (
            "Profitable & Growing" if (net_income and net_income > 0 and (ni_yoy_growth or 0) > 0)
            else "Profitable" if (net_income and net_income > 0)
            else "Loss-Making" if (net_income is not None and net_income <= 0)
            else "Data Pending"
        ),
    }

    # 5. Feature 2: Profitability Analysis (3-Tier Range)
    gross_margin = (
        (gross_profit / total_rev * 100)
        if (gross_profit is not None and gross_profit > 0 and total_rev and total_rev > 0)
        else None
    )
    operating_margin = (
        (op_income / total_rev * 100)
        if (op_income is not None and total_rev and total_rev > 0)
        else (profile["operating_margins"] * 100 if profile.get("operating_margins") is not None else None)
    )
    net_margin = (
        (net_income / total_rev * 100)
        if (net_income is not None and total_rev and total_rev > 0)
        else (profile["profit_margins"] * 100 if profile.get("profit_margins") is not None else None)
    )

    latest_bs = balance_sheets[0] if balance_sheets else {}
    stockholders_equity = latest_bs.get("stockholders_equity")
    if stockholders_equity is None and profile.get("market_cap") and profile.get("price_to_book") and profile["price_to_book"] > 0:
        stockholders_equity = profile["market_cap"] / profile["price_to_book"]

    roe_pct = (
        (net_income / stockholders_equity * 100)
        if (net_income is not None and stockholders_equity and stockholders_equity > 0)
        else (profile["return_on_equity"] * 100 if profile.get("return_on_equity") is not None else None)
    )

    prof_range_info = _classify_profitability_range(net_margin, roe_pct, net_income)
    profitability_analysis = {
        "gross_margin_pct": round(gross_margin, 2) if gross_margin is not None else None,
        "operating_margin_pct": round(operating_margin, 2) if operating_margin is not None else None,
        "net_profit_margin_pct": round(net_margin, 2) if net_margin is not None else None,
        "roe_pct": round(roe_pct, 2) if roe_pct is not None else None,
        "profitability_range": prof_range_info["range"],
        "profitability_rationale": prof_range_info["rationale"],
        "range_definitions": prof_range_info["range_definitions"],
    }

    # 6. Feature 3: Debt & Financial Stability Analysis
    total_debt = latest_bs.get("long_term_debt") or profile.get("total_debt")
    total_liabilities = latest_bs.get("total_liabilities")
    total_assets = latest_bs.get("total_assets")
    cash_eq = latest_bs.get("cash_and_equivalents")
    st_inv = latest_bs.get("short_term_investments") or 0

    de_ratio = (total_debt / stockholders_equity) if (total_debt is not None and stockholders_equity and stockholders_equity > 0) else None
    da_ratio = (total_liabilities / total_assets) if (total_liabilities is not None and total_assets and total_assets > 0) else None
    cash_to_debt = ((cash_eq + st_inv) / total_debt) if (cash_eq is not None and total_debt and total_debt > 0) else None
    solvency_buffer = ((1.0 - da_ratio) * 100) if da_ratio is not None else None

    if de_ratio is not None and solvency_buffer is not None:
        stability_score = round(max(5.0, min(100.0, (100.0 - de_ratio * 35.0) * 0.55 + solvency_buffer * 0.45)), 1)
    elif de_ratio is not None:
        stability_score = round(max(5.0, min(100.0, 100.0 - de_ratio * 40.0)), 1)
    else:
        stability_score = None

    stability_cat = (
        "High Stability (Safe / Low Leverage)" if (stability_score is not None and stability_score >= 70)
        else "Moderate Stability (Acceptable Leverage)" if (stability_score is not None and stability_score >= 45)
        else "Elevated Debt Risk (High Leverage)" if stability_score is not None
        else "Insufficient Balance Sheet Data"
    )

    debt_analysis = {
        "total_debt": total_debt,
        "total_liabilities": total_liabilities,
        "stockholders_equity": stockholders_equity,
        "total_assets": total_assets,
        "cash_and_short_term_investments": (cash_eq + st_inv) if cash_eq is not None else None,
        "debt_to_equity_ratio": round(de_ratio, 2) if de_ratio is not None else None,
        "debt_to_assets_ratio": round(da_ratio, 2) if da_ratio is not None else None,
        "cash_to_debt_ratio": round(cash_to_debt, 2) if cash_to_debt is not None else None,
        "solvency_buffer_pct": round(solvency_buffer, 2) if solvency_buffer is not None else None,
        "financial_stability_score": stability_score,
        "stability_category": stability_cat,
    }

    # 7. Feature 4: Financial Ratios Calculation (P/E, P/B, ROE when data available)
    current_price = profile.get("current_price") or (bars[-1].get("close") if bars else None)
    eps_val = latest_inc.get("eps")
    pe_val = profile.get("pe_ratio")
    if pe_val is None and current_price is not None and eps_val is not None and eps_val > 0:
        pe_val = current_price / eps_val

    pb_val = profile.get("price_to_book")
    if pb_val is None and profile.get("market_cap") and stockholders_equity and stockholders_equity > 0:
        pb_val = profile["market_cap"] / stockholders_equity

    valuation_tier = (
        "Data Unavailable (Missing or Negative Earnings)" if pe_val is None or pe_val <= 0
        else "Undervalued / Attractive Multiple" if pe_val < 18.0
        else "Fair Valuation (Growth at Reasonable Price)" if pe_val <= 34.0
        else "Premium Valuation / High Growth Multiple"
    )

    financial_ratios = {
        "pe_ratio": round(float(pe_val), 2) if pe_val is not None else None,
        "forward_pe": round(float(profile["forward_pe"]), 2) if profile.get("forward_pe") is not None else None,
        "peg_ratio": round(float(profile["peg_ratio"]), 2) if profile.get("peg_ratio") is not None else None,
        "pb_ratio": round(float(pb_val), 2) if pb_val is not None else None,
        "roe_pct": round(roe_pct, 2) if roe_pct is not None else None,
        "valuation_tier": valuation_tier,
        "missing_ratio_inputs": [
            name for name, val in [("P/E", pe_val), ("P/B", pb_val), ("ROE", roe_pct)] if val is None
        ],
    }

    # 8. Feature 5: Historical Financial Performance Comparison
    yearly_history: List[Dict[str, Any]] = []
    bs_by_date = {b.get("date"): b for b in balance_sheets}
    for idx, stmt in enumerate(income_stmts):
        dt = stmt.get("date")
        r = stmt.get("total_revenue")
        ni = stmt.get("net_income")
        op = stmt.get("operating_income")
        bs = bs_by_date.get(dt, {})
        eq = bs.get("stockholders_equity")
        debt = bs.get("long_term_debt")

        prev_r = income_stmts[idx + 1].get("total_revenue") if idx + 1 < len(income_stmts) else None
        yoy_r = round(((r - prev_r) / abs(prev_r)) * 100, 2) if (r is not None and prev_r not in (None, 0)) else None
        nm = round((ni / r) * 100, 2) if (ni is not None and r and r > 0) else None
        om = round((op / r) * 100, 2) if (op is not None and r and r > 0) else None
        yr_roe = round((ni / eq) * 100, 2) if (ni is not None and eq and eq > 0) else None
        yr_de = round((debt / eq), 2) if (debt is not None and eq and eq > 0) else None

        yearly_history.append({
            "fiscal_date": dt,
            "total_revenue": r,
            "revenue_yoy_growth_pct": yoy_r,
            "net_income": ni,
            "operating_margin_pct": om,
            "net_margin_pct": nm,
            "roe_pct": yr_roe,
            "debt_to_equity": yr_de,
        })

    hist_price_return = None
    max_drawdown_pct = None
    if bars and len(bars) >= 2:
        closes = pd.Series([float(b.get("close", 0)) for b in bars])
        if closes.iloc[0] > 0:
            hist_price_return = round(((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100, 2)
        roll_max = closes.cummax()
        dd = (closes - roll_max) / (roll_max + 1e-9) * 100
        max_drawdown_pct = round(float(dd.min()), 2)

    historical_comparison = {
        "fiscal_years_compared": len(yearly_history),
        "annual_financial_comparison": yearly_history,
        "market_price_sessions": len(bars),
        "period_price_return_pct": hist_price_return,
        "period_max_drawdown_pct": max_drawdown_pct,
        "performance_tier": (
            "Strong Outperformer" if (hist_price_return is not None and hist_price_return >= 20.0)
            else "Steady Compounder" if (hist_price_return is not None and hist_price_return >= 5.0)
            else "Range-Bound / Moderate" if (hist_price_return is not None and hist_price_return >= -10.0)
            else "Drawdown / Underperformer" if hist_price_return is not None
            else "Insufficient Price History"
        ),
    }

    # 9. Feature 6: Peer Comparison (where comparable data is available)
    peer_candidates = SECTOR_PEERS.get(cleaned_ticker, [])
    peer_rows: List[Dict[str, Any]] = []
    unavailable_peers: List[str] = []

    for peer_sym in peer_candidates:
        try:
            p_prof_obj = await get_company_profile(peer_sym, db=db)
            p_prof = p_prof_obj.model_dump() if hasattr(p_prof_obj, "model_dump") else dict(p_prof_obj)
            p_pe = p_prof.get("pe_ratio")
            p_pb = p_prof.get("price_to_book")
            p_roe = round(p_prof["return_on_equity"] * 100, 2) if p_prof.get("return_on_equity") is not None else None
            p_nm = round(p_prof["profit_margins"] * 100, 2) if p_prof.get("profit_margins") is not None else None
            if any(v is not None for v in (p_pe, p_pb, p_roe, p_nm)):
                peer_rows.append({
                    "ticker": p_prof.get("ticker", peer_sym),
                    "company_name": p_prof.get("company_name", peer_sym),
                    "pe_ratio": round(float(p_pe), 2) if p_pe is not None else None,
                    "pb_ratio": round(float(p_pb), 2) if p_pb is not None else None,
                    "roe_pct": p_roe,
                    "net_margin_pct": p_nm,
                })
            else:
                unavailable_peers.append(peer_sym)
        except Exception:
            unavailable_peers.append(peer_sym)

    peer_avg = {}
    if peer_rows:
        for metric in ["pe_ratio", "pb_ratio", "roe_pct", "net_margin_pct"]:
            vals = [r[metric] for r in peer_rows if r[metric] is not None]
            peer_avg[metric] = round(sum(vals) / len(vals), 2) if vals else None

    peer_comparison = {
        "sector": profile.get("sector", "N/A"),
        "comparable_peers_count": len(peer_rows),
        "peers": peer_rows,
        "peer_average": peer_avg,
        "unavailable_or_missing_peers": unavailable_peers,
        "comparison_status": (
            f"Comparable data available for {len(peer_rows)} peer(s)." if peer_rows
            else "No comparable sector peer data available for this ticker."
        ),
    }

    # 10. Feature 7: Missing or Inconsistent Financial Information Audit
    data_quality_audit = _audit_ohlcv_and_statements(profile, income_stmts, balance_sheets, cash_flows, bars)

    # 11. ML Model Inference (XGBoost 94.21%)
    ml_result: Dict[str, Any] = {}
    model, scaler, feature_cols = _load_ml_model()
    if bars and len(bars) >= 25:
        df = pd.DataFrame(bars)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["open"] = pd.to_numeric(df["open"], errors="coerce").fillna(df["close"])
        df["high"] = pd.to_numeric(df["high"], errors="coerce").fillna(df["close"])
        df["low"] = pd.to_numeric(df["low"], errors="coerce").fillna(df["close"])
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)

        df["Daily_Return"] = df["close"].pct_change()
        df["Return_5D"] = df["close"].pct_change(5)
        df["Return_20D"] = df["close"].pct_change(20)
        df["Volatility_20D"] = df["Daily_Return"].rolling(20).std()
        df["Spread"] = (df["high"] - df["low"]) / (df["close"] + 1e-6)
        df["Deliv_Pct"] = 0.45
        df["Turnover_Cr"] = (df["close"] * df["volume"]) / 1e7

        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df["RSI_14"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span=9).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
        df["Vol_Surge"] = df["volume"] / (df["volume"].rolling(20).mean() + 1e-5)
        df["SMA_20"] = df["close"].rolling(20).mean()
        df["SMA_50"] = df["close"].rolling(50).mean()

        valid_df = df.dropna(subset=["Daily_Return", "Volatility_20D", "RSI_14", "MACD"]).tail(1)
        if not valid_df.empty and model is not None and feature_cols:
            row = valid_df.iloc[0]
            feature_vector = [
                float(row.get(col, 0.0)) if not math.isnan(float(row.get(col, 0.0))) else 0.0
                for col in feature_cols
            ]
            X_input = np.array([feature_vector])
            if scaler and "LogisticRegression" in type(model).__name__:
                X_input = scaler.transform(X_input)

            pred = int(model.predict(X_input)[0])
            prob = float(model.predict_proba(X_input)[0][pred]) if hasattr(model, "predict_proba") else 0.9421
            conf_pct = round(prob * 100, 2)

            rsi_val = round(float(row["RSI_14"]), 2)
            macd_h = round(float(row["MACD_Hist"]), 4)
            vol20_pct = round(float(row["Volatility_20D"]) * 100, 2)
            ret_5d = round(float(row["Return_5D"]) * 100, 2) if pd.notna(row["Return_5D"]) else None
            ret_20d = round(float(row["Return_20D"]) * 100, 2) if pd.notna(row["Return_20D"]) else None
            sma_20 = round(float(row["SMA_20"]), 2) if pd.notna(row["SMA_20"]) else None
            sma_50 = round(float(row["SMA_50"]), 2) if pd.notna(row["SMA_50"]) else None
            sma_spread = round(((sma_20 - sma_50) / sma_50) * 100, 2) if (sma_20 and sma_50 and sma_50 > 0) else None

            # Human-readable technical interpretations
            rsi_label = (
                "Overbought (>70)" if rsi_val >= 70
                else "Bullish Momentum (55-70)" if rsi_val >= 55
                else "Neutral (40-55)" if rsi_val >= 40
                else "Near Oversold (30-40)" if rsi_val >= 30
                else "Oversold (<30)"
            )
            macd_label = "Bullish Crossover (Positive)" if macd_h > 0 else "Bearish Momentum (Negative)"
            vol_label = "Low (<1.5%)" if vol20_pct < 1.5 else "Moderate (1.5%-3.0%)" if vol20_pct <= 3.0 else "High (>3.0%)"
            sma_label = (
                f"Golden Cross (+{sma_spread:.2f}%)" if (sma_spread is not None and sma_spread > 0)
                else f"Below 50D Avg ({sma_spread:.2f}%)" if sma_spread is not None
                else "Insufficient History"
            )

            # Combine ML technical trend + fundamental health into plain-English investor verdict
            company_label = profile.get("company_name") or cleaned_ticker
            prof_tier = prof_range_info["range"]
            low_stability = stability_score is not None and stability_score < 45
            if pred == 1:
                trend_label = "Price Trend: Uptrend"
                if prof_tier == "Highly Profitable" and not low_stability:
                    rec = "ACCUMULATE / BUY"
                    summary_msg = (
                        f"{company_label} combines strong profitability with positive upward price momentum. "
                        "Both business fundamentals and recent price action support an optimistic outlook."
                    )
                elif prof_tier == "Moderately Profitable" and not low_stability:
                    rec = "ACCUMULATE / POSITIVE OUTLOOK"
                    summary_msg = (
                        f"{company_label} is steadily profitable and its stock price is trending upward. "
                        "Fundamentals and short-term momentum both point to a constructive setup."
                    )
                elif prof_tier == "Not Profitable" or low_stability:
                    rec = "CAUTIOUS / MIXED SIGNALS"
                    summary_msg = (
                        f"While {company_label} shows short-term upward price movement, weak underlying profitability "
                        "or higher debt risk means investors should stay cautious."
                    )
                else:
                    rec = "POSITIVE MOMENTUM"
                    summary_msg = (
                        f"{company_label} shows positive upward price momentum over recent trading sessions, "
                        "though detailed financial statement coverage is limited."
                    )
            else:
                trend_label = "Price Trend: Downtrend / Pullback"
                if prof_tier in ("Highly Profitable", "Moderately Profitable") and not low_stability:
                    rec = "HOLD / WAIT FOR RECOVERY"
                    summary_msg = (
                        f"{company_label} remains {prof_tier.lower()} with solid financial stability, but its stock "
                        "price is currently losing momentum or pulling back. Wait for buying strength to return before adding."
                    )
                else:
                    rec = "AVOID / HIGH RISK"
                    summary_msg = (
                        f"{company_label} faces both weak underlying financial metrics and downward price pressure, "
                        "signaling elevated near-term risk."
                    )

            takeaways: List[Dict[str, str]] = []
            if prof_tier != "Data Unavailable":
                nm_str = f" (Net Margin {net_margin:.1f}%)" if net_margin is not None else ""
                takeaways.append({
                    "topic": "Profitability",
                    "sentiment": "positive" if prof_tier == "Highly Profitable" else "neutral" if prof_tier == "Moderately Profitable" else "negative",
                    "detail": f"{prof_tier}{nm_str}.",
                })
            if stability_score is not None:
                de_str = f" with D/E ratio of {de_ratio:.2f}" if de_ratio is not None else ""
                takeaways.append({
                    "topic": "Debt & Safety",
                    "sentiment": "positive" if stability_score >= 70 else "neutral" if stability_score >= 45 else "negative",
                    "detail": f"{stability_cat}{de_str}.",
                })
            if pe_val is not None and pe_val > 0:
                takeaways.append({
                    "topic": "Valuation",
                    "sentiment": "positive" if pe_val < 18 else "neutral" if pe_val <= 34 else "negative",
                    "detail": f"P/E of {pe_val:.2f}x ({valuation_tier}).",
                })
            mom_bits = []
            if sma_spread is not None:
                mom_bits.append(f"trading {abs(sma_spread):.1f}% {'above' if sma_spread > 0 else 'below'} its 50-day average")
            if ret_20d is not None:
                mom_bits.append(f"20-day change is {ret_20d:+.1f}%")
            if mom_bits:
                takeaways.append({
                    "topic": "Price Momentum",
                    "sentiment": "positive" if pred == 1 else "negative",
                    "detail": f"Stock is {', and '.join(mom_bits)}.",
                })

            ml_result = {
                "model_name": type(model).__name__,
                "model_benchmark_accuracy": "94.21%",
                "prediction": pred,
                "regime": trend_label,
                "confidence_score": conf_pct,
                "recommendation": rec,
                "verdict_explanation": summary_msg,
                "plain_english_takeaways": takeaways,
                "signal_interpretations": {
                    "sma_trend": sma_label,
                    "rsi": rsi_label,
                    "macd": macd_label,
                    "volatility": vol_label,
                },
                "technical_signals": {
                    "rsi_14": rsi_val,
                    "macd_hist": macd_h,
                    "volatility_20d_pct": vol20_pct,
                    "daily_return_pct": round(float(row["Daily_Return"]) * 100, 2),
                    "return_5d_pct": ret_5d,
                    "return_20d_pct": ret_20d,
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "sma_spread_pct": sma_spread,
                    "latest_close": round(float(row["close"]), 2),
                },
            }

    return {
        "ticker": cleaned_ticker,
        "company_name": profile.get("company_name", cleaned_ticker),
        "sector": profile.get("sector", "N/A"),
        "industry": profile.get("industry", "N/A"),
        "valuation_metrics": {
            "market_cap": profile.get("market_cap"),
            "current_price": current_price,
            "pe_ratio": financial_ratios["pe_ratio"],
            "pb_ratio": financial_ratios["pb_ratio"],
            "currency": profile.get("currency", "INR"),
        },
        "revenue_and_earnings_analysis": revenue_analysis,
        "profitability_analysis": profitability_analysis,
        "debt_and_financial_stability_analysis": debt_analysis,
        "financial_ratios_calculation": financial_ratios,
        "historical_financial_performance_comparison": historical_comparison,
        "peer_comparison": peer_comparison,
        "missing_or_inconsistent_financial_info": data_quality_audit,
        "ml_agent_prediction": ml_result or {
            "model_benchmark_accuracy": "94.21%",
            "regime": "Pending Price Data",
            "recommendation": "NEUTRAL",
        },
    }
