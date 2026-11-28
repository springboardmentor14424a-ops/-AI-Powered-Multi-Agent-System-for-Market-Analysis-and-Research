
import pandas as pd
import yfinance as yf

from datetime import datetime, timezone

from app.services.stock_data_service import (
    validate_symbol,
    get_financial_statements,
    get_company_profile,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

DATA_SOURCE = "Yahoo Finance"
MAX_PEERS = 3

# Verified Indian IT companies.
# Symbols are grouped by stock exchange.

INDUSTRY_PEER_MAP = {
    "information technology services": {
        ".NS": [
            "TCS.NS",
            "HCLTECH.NS",
            "WIPRO.NS",
            "TECHM.NS",
        ],
        ".BO": [
            "532540.BO",
            "532281.BO",
            "507685.BO",
            "532755.BO",
        ],
    }
}

PEER_METRIC_NAMES = [
    "revenue_growth_percent",
    "profit_margin_percent",
    "return_on_equity_percent",
    "debt_to_equity_percent",
    "pe_ratio",
    "pb_ratio",
]


# ==========================================================
# HELPER: FIND FINANCIAL ROW
# ==========================================================

def find_financial_value(data, possible_names):

    if data is None or data.empty:
        return None

    for name in possible_names:

        if name in data.index:

            values = data.loc[name]

            if isinstance(values, pd.Series):

                values = pd.to_numeric(
                    values,
                    errors="coerce"
                ).dropna()

                if not values.empty:
                    return float(values.iloc[0])

            elif pd.notna(values):
                return float(values)

    return None


# ==========================================================
# HELPER: HISTORICAL FINANCIAL VALUES
# ==========================================================

def get_historical_values(data, possible_names):

    if data is None or data.empty:
        return []

    for name in possible_names:

        if name in data.index:

            values = data.loc[name]

            if isinstance(values, pd.Series):

                result = []

                for period, value in values.items():

                    if pd.notna(value):

                        result.append({
                            "period": str(period),
                            "value": float(value)
                        })

                return result

    return []


# ==========================================================
# REVENUE AND EARNINGS ANALYSIS
# ==========================================================

def analyze_revenue_and_earnings(income_statement):

    revenue_names = [
        "Total Revenue",
        "Operating Revenue",
        "Revenue"
    ]

    earnings_names = [
        "Net Income",
        "Net Income Common Stockholders",
        "Net Income From Continuing Operation Net Minority Interest"
    ]

    revenue_history = get_historical_values(
        income_statement,
        revenue_names
    )

    earnings_history = get_historical_values(
        income_statement,
        earnings_names
    )

    revenue_growth = None
    earnings_growth = None

    if len(revenue_history) >= 2:

        latest = revenue_history[0]["value"]
        previous = revenue_history[1]["value"]

        if previous != 0:

            revenue_growth = round(
                ((latest - previous) / abs(previous)) * 100,
                2
            )

    if len(earnings_history) >= 2:

        latest = earnings_history[0]["value"]
        previous = earnings_history[1]["value"]

        if previous != 0:

            earnings_growth = round(
                ((latest - previous) / abs(previous)) * 100,
                2
            )

    return {
        "revenue_history": revenue_history,
        "earnings_history": earnings_history,
        "revenue_growth_percent": revenue_growth,
        "earnings_growth_percent": earnings_growth
    }


# ==========================================================
# PROFITABILITY ANALYSIS
# ==========================================================

def analyze_profitability(income_statement, balance_sheet):

    revenue = find_financial_value(
        income_statement,
        ["Total Revenue", "Operating Revenue", "Revenue"]
    )

    net_income = find_financial_value(
        income_statement,
        [
            "Net Income",
            "Net Income Common Stockholders",
            "Net Income From Continuing Operation Net Minority Interest"
        ]
    )

    equity = find_financial_value(
        balance_sheet,
        [
            "Stockholders Equity",
            "Total Stockholder Equity",
            "Total Equity Gross Minority Interest"
        ]
    )

    profit_margin = None
    roe = None

    if revenue is not None and revenue != 0 and net_income is not None:

        profit_margin = round(
            (net_income / revenue) * 100,
            2
        )

    if equity is not None and equity != 0 and net_income is not None:

        roe = round(
            (net_income / equity) * 100,
            2
        )

    return {
        "revenue": revenue,
        "net_income": net_income,
        "profit_margin_percent": profit_margin,
        "return_on_equity_percent": roe
    }


# ==========================================================
# DEBT AND FINANCIAL STABILITY
# ==========================================================

def analyze_financial_stability(balance_sheet):

    total_debt = find_financial_value(
        balance_sheet,
        [
            "Total Debt",
            "Long Term Debt And Capital Lease Obligation"
        ]
    )

    equity = find_financial_value(
        balance_sheet,
        [
            "Stockholders Equity",
            "Total Stockholder Equity",
            "Total Equity Gross Minority Interest"
        ]
    )

    debt_to_equity = None

    if total_debt is not None and equity is not None and equity != 0:

        debt_to_equity = round(
            (total_debt / equity) * 100,
            2
        )

    return {
        "total_debt": total_debt,
        "shareholders_equity": equity,
        "debt_to_equity_percent": debt_to_equity
    }


# ==========================================================
# VALUATION RATIOS
# ==========================================================

def calculate_valuation_ratios(symbol):

    stock = yf.Ticker(symbol)
    info = stock.get_info()

    pe_ratio = info.get("trailingPE")
    pb_ratio = info.get("priceToBook")

    return {
        "pe_ratio": (
            round(float(pe_ratio), 2)
            if pe_ratio is not None else None
        ),
        "pb_ratio": (
            round(float(pb_ratio), 2)
            if pb_ratio is not None else None
        )
    }


# ==========================================================
# HELPER: MARKET SUFFIX
# ==========================================================

def get_market_suffix(symbol):

    symbol = symbol.upper()

    if symbol.endswith(".NS"):
        return ".NS"

    if symbol.endswith(".BO"):
        return ".BO"

    return ""


# ==========================================================
# HELPER: GET COMPANY METRICS
# ==========================================================

def get_company_metrics(symbol):

    statements = get_financial_statements(symbol)

    income_statement = statements.get("income_statement")
    balance_sheet = statements.get("balance_sheet")

    revenue_earnings = analyze_revenue_and_earnings(
        income_statement
    )

    profitability = analyze_profitability(
        income_statement,
        balance_sheet
    )

    financial_stability = analyze_financial_stability(
        balance_sheet
    )

    valuation = calculate_valuation_ratios(symbol)

    return {
        "revenue_growth_percent":
            revenue_earnings["revenue_growth_percent"],

        "profit_margin_percent":
            profitability["profit_margin_percent"],

        "return_on_equity_percent":
            profitability["return_on_equity_percent"],

        "debt_to_equity_percent":
            financial_stability["debt_to_equity_percent"],

        "pe_ratio":
            valuation["pe_ratio"],

        "pb_ratio":
            valuation["pb_ratio"]
    }


# ==========================================================
# HELPER: GET PEER CANDIDATES
# ==========================================================

def get_peer_candidates(symbol, industry):

    market_suffix = get_market_suffix(symbol)

    industry_key = industry.lower().strip()

    industry_mapping = INDUSTRY_PEER_MAP.get(industry_key, {})

    candidates = industry_mapping.get(market_suffix, [])

    # Use Yahoo Search as a fallback for industries
    # without a predefined peer mapping.

    if not candidates:

        try:

            search_results = yf.Search(
                industry,
                max_results=20
            )

            quotes = getattr(
                search_results,
                "quotes",
                []
            ) or []

            for item in quotes:

                peer_symbol = item.get("symbol")

                if not peer_symbol:
                    continue

                peer_symbol = peer_symbol.upper()

                if get_market_suffix(peer_symbol) == market_suffix:
                    candidates.append(peer_symbol)

        except Exception:
            pass

    return candidates


# ==========================================================
# HELPER: CALCULATE PEER AVERAGES
# ==========================================================

def calculate_peer_averages(peers):

    averages = {}

    for metric in PEER_METRIC_NAMES:

        values = []

        for peer in peers:

            value = peer["metrics"].get(metric)

            if value is not None:

                values.append(float(value))

        if values:

            averages[metric] = round(
                sum(values) / len(values),
                2
            )

        else:

            averages[metric] = None

    return averages


# ==========================================================
# PEER COMPARISON
# ==========================================================

def analyze_peer_comparison(symbol, profile, company_metrics):

    industry = profile.get("industry")

    if not industry:

        return {
            "status": "unavailable",
            "message": "Industry information is unavailable.",
            "peer_count": 0,
            "peers": []
        }

    candidates = get_peer_candidates(
        symbol,
        industry
    )

    peers = []

    for peer_symbol in candidates:

        peer_symbol = peer_symbol.upper()

        # Do not compare the company with itself.

        if peer_symbol == symbol.upper():
            continue

        try:

            peer_profile = get_company_profile(peer_symbol)

            peer_industry = peer_profile.get("industry")

            # Compare only companies with matching industries.

            if (
                not peer_industry
                or peer_industry.strip().lower()
                != industry.strip().lower()
            ):
                continue

            peer_metrics = get_company_metrics(peer_symbol)

            # Skip companies that do not return any useful metrics.

            if not any(
                value is not None
                for value in peer_metrics.values()
            ):
                continue

            peers.append({
                "symbol": peer_symbol,

                "company_name": (
                    peer_profile.get("longName")
                    or peer_profile.get("shortName")
                    or peer_symbol
                ),

                "industry": peer_industry,

                "metrics": peer_metrics
            })

            if len(peers) >= MAX_PEERS:
                break

        except Exception as error:

            print(
                f"Skipping peer {peer_symbol}: {error}"
            )

            continue

    if not peers:

        return {
            "status": "unavailable",
            "message": (
                "No comparable companies with sufficient "
                "financial data were found."
            ),
            "peer_count": 0,
            "peers": []
        }

    peer_averages = calculate_peer_averages(peers)

    return {
        "status": "available",

        "comparison_basis": (
            "Companies with matching industry "
            "and stock exchange"
        ),

        "peer_count": len(peers),

        "company_metrics": company_metrics,

        "peer_average_metrics": peer_averages,

        "peers": peers
    }


# ==========================================================
# DATA QUALITY CHECK
# ==========================================================

def identify_missing_information(analysis):

    missing = []

    checks = {
        "Revenue": analysis["revenue_earnings"]["revenue_history"],
        "Earnings": analysis["revenue_earnings"]["earnings_history"],
        "Profit Margin": analysis["profitability"]["profit_margin_percent"],
        "ROE": analysis["profitability"]["return_on_equity_percent"],
        "Debt to Equity": analysis["financial_stability"]["debt_to_equity_percent"],
        "P/E Ratio": analysis["valuation"]["pe_ratio"],
        "P/B Ratio": analysis["valuation"]["pb_ratio"]
    }

    for name, value in checks.items():

        if value is None or value == []:

            missing.append(
                f"{name} data is unavailable"
            )

    return missing


# ==========================================================
# MAIN FUNDAMENTAL ANALYSIS AGENT
# ==========================================================

def run_fundamental_analysis(symbol):

    symbol = validate_symbol(symbol)

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    # Retrieve existing financial data.

    statements = get_financial_statements(symbol)

    profile = get_company_profile(symbol)

    income_statement = statements["income_statement"]

    balance_sheet = statements["balance_sheet"]

    # Perform individual analyses.

    revenue_earnings = analyze_revenue_and_earnings(
        income_statement
    )

    profitability = analyze_profitability(
        income_statement,
        balance_sheet
    )

    financial_stability = analyze_financial_stability(
        balance_sheet
    )

    valuation = calculate_valuation_ratios(symbol)

    company_metrics = {
        "revenue_growth_percent":
            revenue_earnings["revenue_growth_percent"],

        "profit_margin_percent":
            profitability["profit_margin_percent"],

        "return_on_equity_percent":
            profitability["return_on_equity_percent"],

        "debt_to_equity_percent":
            financial_stability["debt_to_equity_percent"],

        "pe_ratio":
            valuation["pe_ratio"],

        "pb_ratio":
            valuation["pb_ratio"]
    }

    analysis = {
        "symbol": symbol,

        "company_name": (
            profile.get("longName")
            or profile.get("shortName")
            or symbol
        ),

        "sector": profile.get("sector"),

        "industry": profile.get("industry"),

        "revenue_earnings": revenue_earnings,

        "profitability": profitability,

        "financial_stability": financial_stability,

        "valuation": valuation
    }

    # Perform peer comparison.

    peer_comparison = analyze_peer_comparison(
        symbol,
        profile,
        company_metrics
    )

    analysis["peer_comparison"] = peer_comparison

    # Identify missing information.

    missing_information = identify_missing_information(
        analysis
    )

    analysis["data_quality"] = {
        "missing_information": missing_information,
        "has_missing_data": len(missing_information) > 0
    }

    analysis["metadata"] = {
        "source": DATA_SOURCE,
        "retrieved_at": retrieved_at
    }

    return analysis
