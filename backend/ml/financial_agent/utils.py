"""
utils.py
---------
Module 3 – Financial Agent | Shared Financial Utilities

Reusable mathematical, data extraction, normalization, and scaling utilities
shared across the Financial Agent analytical features.

Principles:
  - Never silently substitute zero for missing data.
  - Safe against division-by-zero, empty inputs, and NaN.
  - Returns None / np.nan when calculations cannot be mathematically performed.
  - Currency-aware and scale-aware (never convert currencies without FX quotes).
  - Works with standard Python types, NumPy types, and Pandas structures.
"""

from datetime import datetime
import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. MATHEMATICAL & ARITHMETIC UTILITIES
# ---------------------------------------------------------------------------

def is_valid_number(val: Any) -> bool:
    """
    Check if a value is a valid, usable real number (not None, not NaN, not infinite).
    """
    if val is None:
        return False
    if isinstance(val, (bool, str)):
        return False
    try:
        f = float(val)
        return not (math.isnan(f) or math.isinf(f))
    except (ValueError, TypeError):
        return False


def safe_divide(
    numerator: Any,
    denominator: Any,
    decimals: Optional[int] = 4,
    default: Any = None,
) -> Optional[float]:
    """
    Safely divide two numbers.

    Returns:
        float if both numerator and denominator are valid and denominator != 0.
        default (default: None) if denominator == 0 or either input is missing/NaN.

    Note:
        Does NOT silently return 0.0 for division-by-zero or missing inputs.
    """
    if not is_valid_number(numerator) or not is_valid_number(denominator):
        return default

    num = float(numerator)
    den = float(denominator)

    if den == 0.0:
        return default

    result = num / den
    if decimals is not None:
        return round(result, decimals)
    return result


def safe_pct_ratio(
    numerator: Any,
    denominator: Any,
    decimals: Optional[int] = 4,
    default: Any = None,
) -> Optional[float]:
    """
    Calculate a percentage ratio: (numerator / denominator) * 100.
    Useful for margins (Gross Margin %, Operating Margin %, Net Margin %, ROE %).
    """
    ratio = safe_divide(numerator, denominator, decimals=None, default=None)
    if ratio is None:
        return default
    pct = ratio * 100.0
    return round(pct, decimals) if decimals is not None else pct


def safe_pct_change(
    current: Any,
    previous: Any,
    decimals: Optional[int] = 4,
    default: Any = None,
) -> Optional[float]:
    """
    Calculate year-over-year or period-over-period percentage growth:
        ((current - previous) / abs(previous)) * 100

    Rules:
        - If previous == 0: percentage growth is undefined mathematically -> returns default.
        - If either value is None, NaN, or non-numeric -> returns default.
        - Preserves correct sign for swings (e.g. from negative to positive).
    """
    if not is_valid_number(current) or not is_valid_number(previous):
        return default

    cur = float(current)
    prev = float(previous)

    if prev == 0.0:
        return default

    pct = ((cur - prev) / abs(prev)) * 100.0
    return round(pct, decimals) if decimals is not None else pct


def safe_diff(
    current: Any,
    previous: Any,
    decimals: Optional[int] = 4,
    default: Any = None,
) -> Optional[float]:
    """
    Calculate absolute difference (current - previous).
    Returns default if either input is invalid.
    """
    if not is_valid_number(current) or not is_valid_number(previous):
        return default
    diff = float(current) - float(previous)
    return round(diff, decimals) if decimals is not None else diff


# ---------------------------------------------------------------------------
# 2. METRIC EXTRACTION & FALLBACKS
# ---------------------------------------------------------------------------

def get_metric(
    data: Union[pd.DataFrame, Dict[str, Any]],
    possible_names: Sequence[str],
    period: Optional[str] = None,
    default: Any = None,
) -> Any:
    """
    Extract a metric using a list of alternative candidate names.

    Supports:
        1. Statement DataFrame where rows = metric names, columns = period dates
           (e.g., raw yfinance income_stmt or balance_sheet).
        2. Processed DataFrame where columns = metric names, rows = periods
           (e.g., reliance_profitability_analysis.csv).
        3. Dict structure (flat or nested by period).

    Args:
        data: Statement DataFrame or dict.
        possible_names: Ordered list of candidate names (e.g. ["Total Revenue", "Operating Revenue"]).
        period: Target period string (e.g. "2026-03-31"). If None, uses the first/latest period.
        default: Value returned if metric is not found or is NaN.

    Returns:
        Metric value if found and valid, else default.
    """
    if data is None:
        return default

    # Case A: Pandas DataFrame
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return default

        # Mode 1: Rows are line items (raw yfinance format: index has metric names)
        for name in possible_names:
            if name in data.index:
                if period is not None and period in data.columns:
                    val = data.loc[name, period]
                    if is_valid_number(val):
                        return float(val)
                elif period is None and len(data.columns) > 0:
                    # Scan across columns (latest first)
                    for col in data.columns:
                        val = data.loc[name, col]
                        if is_valid_number(val):
                            return float(val)

        # Mode 2: Columns are line items (processed table format: columns has metric names)
        for name in possible_names:
            if name in data.columns:
                if period is not None and "Financial_Year" in data.columns:
                    sub = data[data["Financial_Year"].astype(str) == str(period)]
                    if not sub.empty:
                        val = sub.iloc[0][name]
                        if is_valid_number(val):
                            return float(val)
                elif period is None:
                    # Latest row
                    val = data[name].iloc[-1]
                    if is_valid_number(val):
                        return float(val)

    # Case B: Python Dict
    elif isinstance(data, dict):
        # Check flat dict
        for name in possible_names:
            if name in data:
                val = data[name]
                if is_valid_number(val):
                    return float(val)

        # Check nested dict: {period: {metric: value}}
        if period is not None and period in data and isinstance(data[period], dict):
            for name in possible_names:
                if name in data[period]:
                    val = data[period][name]
                    if is_valid_number(val):
                        return float(val)

    return default


# ---------------------------------------------------------------------------
# 3. PERIOD NORMALIZATION & SORTING
# ---------------------------------------------------------------------------

def normalize_periods(
    periods: Iterable[Any],
    descending: bool = False,
) -> List[str]:
    """
    Standardize and sort a collection of financial period dates.

    Rules:
        - Parses date formats into standard 'YYYY-MM-DD' strings.
        - Deduplicates identical periods while preserving ordering.
        - Sorts chronologically (earliest to latest) by default; or latest-first if descending=True.
        - Ignores invalid/unparseable values (never invents missing periods).
    """
    valid_dates: List[Tuple[datetime, str]] = []

    for p in periods:
        if p is None or pd.isna(p):
            continue
        # Convert to string and strip
        p_str = str(p).strip()
        if not p_str or p_str.lower() in ("nan", "none", "nat"):
            continue

        try:
            dt = pd.to_datetime(p_str)
            if not pd.isna(dt):
                formatted = dt.strftime("%Y-%m-%d")
                valid_dates.append((dt.to_pydatetime(), formatted))
        except Exception:
            continue

    # Deduplicate by formatted string while maintaining sort order
    seen = set()
    sorted_pairs = sorted(valid_dates, key=lambda x: x[0], reverse=descending)

    result: List[str] = []
    for _, fmt in sorted_pairs:
        if fmt not in seen:
            seen.add(fmt)
            result.append(fmt)

    return result


# ---------------------------------------------------------------------------
# 4. CURRENCY & UNIT SCALING HELPERS
# ---------------------------------------------------------------------------

# Conversion factors (within-currency scale only; no cross-currency FX)
INR_CRORE = 1e7       # 1 Crore = 10,000,000 INR
INR_LAKH  = 1e5       # 1 Lakh  = 100,000 INR
USD_MILLION = 1e6     # 1 Million USD
USD_BILLION = 1e9     # 1 Billion USD


def scale_currency_amount(
    amount: Any,
    currency: str = "INR",
    target_scale: Optional[str] = None,
    decimals: int = 2,
) -> Tuple[Optional[float], str]:
    """
    Scale a monetary amount into a human-readable reporting unit.

    Rules:
        - NEVER applies exchange rates (FX) without explicit quotes.
        - For INR:
            - Default scale is 'crore' / 'cr' (divides by 10^7).
            - Scale label: 'INR Cr'.
        - For USD:
            - If amount >= 1 Billion or target_scale == 'billion': divides by 10^9 ('USD B').
            - Otherwise divides by 10^6 ('USD M').
        - Returns (None, unit_label) if amount is missing/invalid.

    Returns:
        (scaled_numeric_value, unit_label)
    """
    curr = (currency or "INR").strip().upper()
    unit_label = curr

    if not is_valid_number(amount):
        return None, unit_label

    val = float(amount)

    if curr == "INR":
        scale = (target_scale or "crore").lower()
        if scale in ("crore", "cr"):
            scaled = val / INR_CRORE
            return round(scaled, decimals), "INR Cr"
        elif scale in ("lakh", "lac"):
            scaled = val / INR_LAKH
            return round(scaled, decimals), "INR Lakh"
        else:
            return round(val, decimals), "INR"

    elif curr == "USD":
        scale = (target_scale or "").lower()
        if scale in ("billion", "b") or (not scale and abs(val) >= USD_BILLION):
            scaled = val / USD_BILLION
            return round(scaled, decimals), "USD B"
        elif scale in ("million", "m") or (not scale and abs(val) >= USD_MILLION):
            scaled = val / USD_MILLION
            return round(scaled, decimals), "USD M"
        else:
            return round(val, decimals), "USD"

    # Default fallback for other currencies (EUR, GBP, JPY) without hardcoded scale
    return round(val, decimals), curr


def format_currency_display(
    amount: Any,
    currency: str = "INR",
    target_scale: Optional[str] = None,
    decimals: int = 2,
    placeholder: str = "—",
) -> str:
    """
    Format a currency amount into a clean display string (e.g. '₹1,057,219.00 Cr' or '$12.50 B').
    """
    scaled_val, unit_label = scale_currency_amount(amount, currency, target_scale, decimals)
    if scaled_val is None:
        return placeholder

    curr = (currency or "INR").strip().upper()
    symbol = "₹" if curr == "INR" else ("$" if curr == "USD" else f"{curr} ")

    formatted_num = f"{scaled_val:,.{decimals}f}"

    if "Cr" in unit_label:
        return f"{symbol}{formatted_num} Cr"
    elif "Lakh" in unit_label:
        return f"{symbol}{formatted_num} Lakh"
    elif "B" in unit_label:
        return f"{symbol}{formatted_num} B"
    elif "M" in unit_label:
        return f"{symbol}{formatted_num} M"

    return f"{symbol}{formatted_num}"


# ---------------------------------------------------------------------------
# 5. MULTI-PERIOD TREND EVALUATION
# ---------------------------------------------------------------------------

def trend_direction(
    values: Sequence[Any],
    min_delta: float = 0.05,
) -> str:
    """
    Classify the trajectory of a sequence of chronological numeric values.

    Returns:
        - 'Improving'                 : All consecutive changes are positive (> min_delta).
        - 'Declining'                 : All consecutive changes are negative (< -min_delta).
        - 'Stable'                    : All consecutive changes are within [-min_delta, min_delta].
        - 'Improving (with flat lags)': Net positive without any negative steps.
        - 'Declining (with flat lags)': Net negative without any positive steps.
        - 'Mixed'                     : Sequence contains both positive and negative movements.
        - 'Insufficient Data'         : Fewer than 2 valid numeric points available.
    """
    valid = [float(v) for v in values if is_valid_number(v)]
    if len(valid) < 2:
        return "Insufficient Data"

    diffs = [valid[i] - valid[i - 1] for i in range(1, len(valid))]
    pos = sum(d > min_delta for d in diffs)
    neg = sum(d < -min_delta for d in diffs)
    zero = sum(abs(d) <= min_delta for d in diffs)
    n = len(diffs)

    if pos == n:
        return "Improving"
    elif neg == n:
        return "Declining"
    elif zero == n:
        return "Stable"
    elif pos > 0 and neg == 0:
        return "Improving (with flat lags)"
    elif neg > 0 and pos == 0:
        return "Declining (with flat lags)"
    else:
        return "Mixed"
