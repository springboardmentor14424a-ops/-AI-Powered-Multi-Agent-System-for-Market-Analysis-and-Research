"""
Financial Ratio Calculation Engine.
Calculates key financial metrics:
- P/E (Price-to-Earnings)
- EPS (Earnings Per Share)
- ROE (Return on Equity)
- Debt-to-Equity (D/E)
- Current Ratio
- Net Profit Margin
- ROA (Return on Assets)

Provides rigorous input validation, edge case & zero-division handling,
raw formula calculation functions, and live real-data fetch & extraction.
"""

from typing import Dict, Any, Optional, Union
import math
import yfinance as yf


class FinancialRatioValidationError(ValueError):
    """Raised when financial inputs are invalid or unparseable."""
    pass


def _validate_numeric(val: Any, field_name: str, allow_zero: bool = True) -> float:
    """Validates that an input is a finite float/int."""
    if val is None:
        raise FinancialRatioValidationError(f"'{field_name}' cannot be None.")
    try:
        f = float(val)
    except (ValueError, TypeError):
        raise FinancialRatioValidationError(f"'{field_name}' must be a numeric value, got {type(val).__name__}.")
    
    if math.isnan(f) or math.isinf(f):
        raise FinancialRatioValidationError(f"'{field_name}' must be finite, got {f}.")
    
    if not allow_zero and f == 0.0:
        raise FinancialRatioValidationError(f"'{field_name}' cannot be zero (division by zero).")
    
    return f


# =====================================================================
# Core Mathematical Ratio Calculations with Validation & Error Handling
# =====================================================================

def calculate_pe_ratio(price: Union[int, float], eps: Union[int, float]) -> Optional[float]:
    """
    P/E Ratio = Share Price / Earnings Per Share (EPS)
    Returns None if EPS <= 0 (negative earnings indicate company is operating at a loss).
    """
    p = _validate_numeric(price, "price")
    e = _validate_numeric(eps, "eps")
    
    if p < 0:
        raise FinancialRatioValidationError("Price cannot be negative.")
    if e <= 0:
        # P/E is undefined / not meaningful for companies with zero or negative net income
        return None
    return round(p / e, 4)


def calculate_eps(net_income: Union[int, float], weighted_shares_outstanding: Union[int, float]) -> float:
    """
    EPS = Net Income / Weighted Average Shares Outstanding
    """
    ni = _validate_numeric(net_income, "net_income")
    shares = _validate_numeric(weighted_shares_outstanding, "weighted_shares_outstanding", allow_zero=False)
    
    if shares <= 0:
        raise FinancialRatioValidationError("Shares outstanding must be greater than zero.")
    return round(ni / shares, 4)


def calculate_roe(net_income: Union[int, float], total_shareholder_equity: Union[int, float], as_percentage: bool = True) -> Optional[float]:
    """
    ROE = (Net Income / Total Shareholder Equity) [* 100 if percentage]
    Returns None if equity is zero or negative (distorted leverage).
    """
    ni = _validate_numeric(net_income, "net_income")
    equity = _validate_numeric(total_shareholder_equity, "total_shareholder_equity")
    
    if equity <= 0:
        # Negative equity distorts ROE; not meaningful
        return None
    val = (ni / equity) * (100.0 if as_percentage else 1.0)
    return round(val, 4)


def calculate_debt_to_equity(total_debt: Union[int, float], total_shareholder_equity: Union[int, float]) -> Optional[float]:
    """
    Debt-to-Equity = Total Debt / Total Shareholder Equity
    Returns None if equity is zero or negative.
    """
    debt = _validate_numeric(total_debt, "total_debt")
    equity = _validate_numeric(total_shareholder_equity, "total_shareholder_equity")
    
    if debt < 0:
        raise FinancialRatioValidationError("Total debt cannot be negative.")
    if equity <= 0:
        return None
    return round(debt / equity, 4)


def calculate_current_ratio(current_assets: Union[int, float], current_liabilities: Union[int, float]) -> float:
    """
    Current Ratio = Current Assets / Current Liabilities
    """
    assets = _validate_numeric(current_assets, "current_assets")
    liab = _validate_numeric(current_liabilities, "current_liabilities", allow_zero=False)
    
    if assets < 0 or liab < 0:
        raise FinancialRatioValidationError("Current assets and current liabilities cannot be negative.")
    return round(assets / liab, 4)


def calculate_net_profit_margin(net_income: Union[int, float], total_revenue: Union[int, float], as_percentage: bool = True) -> float:
    """
    Net Profit Margin = (Net Income / Total Revenue) [* 100 if percentage]
    """
    ni = _validate_numeric(net_income, "net_income")
    rev = _validate_numeric(total_revenue, "total_revenue", allow_zero=False)
    
    if rev <= 0:
        raise FinancialRatioValidationError("Total revenue must be positive.")
    val = (ni / rev) * (100.0 if as_percentage else 1.0)
    return round(val, 4)


def calculate_roa(net_income: Union[int, float], total_assets: Union[int, float], as_percentage: bool = True) -> float:
    """
    ROA = (Net Income / Total Assets) [* 100 if percentage]
    """
    ni = _validate_numeric(net_income, "net_income")
    assets = _validate_numeric(total_assets, "total_assets", allow_zero=False)
    
    if assets <= 0:
        raise FinancialRatioValidationError("Total assets must be positive.")
    val = (ni / assets) * (100.0 if as_percentage else 1.0)
    return round(val, 4)


# =====================================================================
# High-Level Real Data Fetching & Ratio Evaluation
# =====================================================================

def compute_all_financial_ratios(
    price: Optional[float] = None,
    net_income: Optional[float] = None,
    shares_outstanding: Optional[float] = None,
    total_shareholder_equity: Optional[float] = None,
    total_debt: Optional[float] = None,
    current_assets: Optional[float] = None,
    current_liabilities: Optional[float] = None,
    total_revenue: Optional[float] = None,
    total_assets: Optional[float] = None,
    eps_override: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes all 7 financial ratios from explicit financial statement inputs.
    Gracefully handles missing or zero denominator fields.
    """
    results = {}
    errors = {}

    # 1. EPS
    computed_eps = eps_override
    if computed_eps is None and net_income is not None and shares_outstanding is not None:
        try:
            computed_eps = calculate_eps(net_income, shares_outstanding)
            results["eps"] = computed_eps
        except FinancialRatioValidationError as e:
            errors["eps"] = str(e)
            results["eps"] = None
    else:
        results["eps"] = computed_eps

    # 2. P/E Ratio
    if price is not None and computed_eps is not None:
        try:
            results["pe_ratio"] = calculate_pe_ratio(price, computed_eps)
        except FinancialRatioValidationError as e:
            errors["pe_ratio"] = str(e)
            results["pe_ratio"] = None
    else:
        results["pe_ratio"] = None

    # 3. ROE
    if net_income is not None and total_shareholder_equity is not None:
        try:
            results["roe"] = calculate_roe(net_income, total_shareholder_equity)
        except FinancialRatioValidationError as e:
            errors["roe"] = str(e)
            results["roe"] = None
    else:
        results["roe"] = None

    # 4. Debt-to-Equity
    if total_debt is not None and total_shareholder_equity is not None:
        try:
            results["debt_to_equity"] = calculate_debt_to_equity(total_debt, total_shareholder_equity)
        except FinancialRatioValidationError as e:
            errors["debt_to_equity"] = str(e)
            results["debt_to_equity"] = None
    else:
        results["debt_to_equity"] = None

    # 5. Current Ratio
    if current_assets is not None and current_liabilities is not None:
        try:
            results["current_ratio"] = calculate_current_ratio(current_assets, current_liabilities)
        except FinancialRatioValidationError as e:
            errors["current_ratio"] = str(e)
            results["current_ratio"] = None
    else:
        results["current_ratio"] = None

    # 6. Net Profit Margin
    if net_income is not None and total_revenue is not None:
        try:
            results["net_profit_margin"] = calculate_net_profit_margin(net_income, total_revenue)
        except FinancialRatioValidationError as e:
            errors["net_profit_margin"] = str(e)
            results["net_profit_margin"] = None
    else:
        results["net_profit_margin"] = None

    # 7. ROA
    if net_income is not None and total_assets is not None:
        try:
            results["roa"] = calculate_roa(net_income, total_assets)
        except FinancialRatioValidationError as e:
            errors["roa"] = str(e)
            results["roa"] = None
    else:
        results["roa"] = None

    return {
        "ratios": results,
        "calculation_errors": errors,
    }


def fetch_and_calculate_real_financial_ratios(symbol: str) -> Dict[str, Any]:
    """
    Fetches live real financial statement data for a given ticker symbol
    from Yahoo Finance and computes all 7 target financial ratios.
    """
    sym = symbol.upper().strip()
    ticker = yf.Ticker(sym)
    
    try:
        info = ticker.info or {}
    except Exception as e:
        info = {}

    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    
    # Try getting financial statement tables first, fallback to info metrics
    net_income = None
    total_revenue = info.get("totalRevenue")
    total_assets = None
    total_equity = None
    total_debt = info.get("totalDebt")
    current_assets = None
    current_liabilities = None
    shares_outstanding = info.get("sharesOutstanding")

    try:
        bs = ticker.balance_sheet
        if bs is not None and not bs.empty:
            latest_col = bs.columns[0]
            if "Total Assets" in bs.index:
                total_assets = float(bs.loc["Total Assets", latest_col])
            if "Stockholders Equity" in bs.index:
                total_equity = float(bs.loc["Stockholders Equity", latest_col])
            elif "Total Stockholder Equity" in bs.index:
                total_equity = float(bs.loc["Total Stockholder Equity", latest_col])
            if "Current Assets" in bs.index:
                current_assets = float(bs.loc["Current Assets", latest_col])
            if "Current Liabilities" in bs.index:
                current_liabilities = float(bs.loc["Current Liabilities", latest_col])
            if total_debt is None and "Total Debt" in bs.index:
                total_debt = float(bs.loc["Total Debt", latest_col])
    except Exception:
        pass

    try:
        income_stmt = ticker.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            latest_col = income_stmt.columns[0]
            if "Net Income" in income_stmt.index:
                net_income = float(income_stmt.loc["Net Income", latest_col])
            if total_revenue is None and "Total Revenue" in income_stmt.index:
                total_revenue = float(income_stmt.loc["Total Revenue", latest_col])
    except Exception:
        pass

    # Direct fallback from info if statements were incomplete
    eps_val = info.get("trailingEps") or info.get("forwardEps")
    pe_val = info.get("trailingPE") or info.get("forwardPE")
    roe_val = info.get("returnOnEquity")
    roa_val = info.get("returnOnAssets")
    curr_ratio_val = info.get("currentRatio")
    profit_margin_val = info.get("profitMargins")
    debt_to_equity_val = info.get("debtToEquity")

    # Compute from raw values
    computed = compute_all_financial_ratios(
        price=price,
        net_income=net_income,
        shares_outstanding=shares_outstanding,
        total_shareholder_equity=total_equity,
        total_debt=total_debt,
        current_assets=current_assets,
        current_liabilities=current_liabilities,
        total_revenue=total_revenue,
        total_assets=total_assets,
        eps_override=eps_val,
    )

    ratios = computed["ratios"]

    # Fill any gaps using authoritative provider fields (converted to consistent units)
    if ratios.get("pe_ratio") is None and pe_val is not None:
        ratios["pe_ratio"] = round(float(pe_val), 4)
    if ratios.get("eps") is None and eps_val is not None:
        ratios["eps"] = round(float(eps_val), 4)
    if ratios.get("roe") is None and roe_val is not None:
        ratios["roe"] = round(float(roe_val) * 100.0, 4)
    if ratios.get("roa") is None and roa_val is not None:
        ratios["roa"] = round(float(roa_val) * 100.0, 4)
    if ratios.get("current_ratio") is None and curr_ratio_val is not None:
        ratios["current_ratio"] = round(float(curr_ratio_val), 4)
    if ratios.get("net_profit_margin") is None and profit_margin_val is not None:
        ratios["net_profit_margin"] = round(float(profit_margin_val) * 100.0, 4)
    if ratios.get("debt_to_equity") is None and debt_to_equity_val is not None:
        # yfinance reports debtToEquity in percentage (e.g. 84.28 meaning 0.8428 or 84.28%)
        d_val = float(debt_to_equity_val)
        ratios["debt_to_equity"] = round(d_val / 100.0 if d_val > 5.0 else d_val, 4)

    return {
        "symbol": sym,
        "company_name": info.get("shortName") or info.get("longName", ""),
        "currency": info.get("currency", "USD"),
        "price": price,
        "financial_ratios": {
            "pe_ratio": {
                "value": ratios.get("pe_ratio"),
                "display": f"{ratios.get('pe_ratio'):.2f}x" if ratios.get("pe_ratio") is not None else "N/A (Operating at Loss)",
                "description": "Price to Earnings ratio (Market Value per Share / EPS)",
            },
            "eps": {
                "value": ratios.get("eps"),
                "display": f"${ratios.get('eps'):.2f}" if ratios.get("eps") is not None else "N/A",
                "description": "Earnings Per Share (Net Income / Shares Outstanding)",
            },
            "roe": {
                "value": ratios.get("roe"),
                "display": f"{ratios.get('roe'):.2f}%" if ratios.get("roe") is not None else "N/A",
                "description": "Return on Equity (Net Income / Shareholder Equity)",
            },
            "debt_to_equity": {
                "value": ratios.get("debt_to_equity"),
                "display": f"{ratios.get('debt_to_equity'):.2f}" if ratios.get("debt_to_equity") is not None else "N/A",
                "description": "Debt-to-Equity ratio (Total Debt / Shareholder Equity)",
            },
            "current_ratio": {
                "value": ratios.get("current_ratio"),
                "display": f"{ratios.get('current_ratio'):.2f}" if ratios.get("current_ratio") is not None else "N/A",
                "description": "Current Ratio (Current Assets / Current Liabilities)",
            },
            "net_profit_margin": {
                "value": ratios.get("net_profit_margin"),
                "display": f"{ratios.get('net_profit_margin'):.2f}%" if ratios.get("net_profit_margin") is not None else "N/A",
                "description": "Net Profit Margin (Net Income / Total Revenue)",
            },
            "roa": {
                "value": ratios.get("roa"),
                "display": f"{ratios.get('roa'):.2f}%" if ratios.get("roa") is not None else "N/A",
                "description": "Return on Assets (Net Income / Total Assets)",
            },
        },
        "raw_financials": {
            "total_revenue": total_revenue,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_shareholder_equity": total_equity,
            "total_debt": total_debt,
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "shares_outstanding": shares_outstanding,
        },
    }
