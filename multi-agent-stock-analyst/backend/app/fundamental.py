from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd

from app.agents.fundamental_agent import fundamental_agent
from app.services.valuation_service import get_valuation

router = APIRouter(
    prefix="/fundamental",
    tags=["Fundamental Analysis"]
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sector_info(name):
    """Return (sector, industry) from Yahoo Finance, or (None, None)."""
    try:
        v = get_valuation(name)
        return v.get("sector"), v.get("industry")
    except Exception:
        return None, None


def _pct(value):
    """Convert a stored fraction (0.12) to a percentage (12.0)."""
    if value is None:
        return None
    return round(float(value) * 100, 2)


# ---------------------------------------------------------------------------
# Basic endpoints
# ---------------------------------------------------------------------------

@router.get("/analyze/{company_name}")
def analyze_company(company_name: str):
    try:
        return fundamental_agent.analyze_company(company_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Fundamental analysis failed: {str(error)}"
        )


@router.get("/valuation")
def valuation(company: str):
    """Current P/E, P/B and ROE from Yahoo Finance for any company name."""
    try:
        return get_valuation(company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Yahoo Finance error: {e}")


@router.get("/companies")
def get_companies(search: str = ""):
    companies = fundamental_agent.financial_df[
        "Company"
    ].dropna().unique().tolist()

    search = search.strip().casefold()

    if search:
        companies = [
            company for company in companies
            if search in company.casefold()
        ]

    return {"companies": sorted(companies)[:15]}


# ---------------------------------------------------------------------------
# Report building blocks
# ---------------------------------------------------------------------------

def get_company_history(company_name):
    df = fundamental_agent.financial_df.copy()

    company = df[
        df["Company"].str.casefold() == company_name.strip().casefold()
    ].copy()

    if company.empty:
        raise ValueError(f"Company '{company_name}' was not found.")

    company["Year"] = pd.to_numeric(company["Year"], errors="coerce")
    company = company.dropna(subset=["Year"]).sort_values("Year")

    if company.empty:
        raise ValueError("No valid financial-year records found.")

    # Absolute-value columns (rounded to 2 decimals)
    amount_columns = [
        "Sales", "Net profit", "Profit before tax",
        "Operating Profit", "Borrowings",
        "Cash from Operating Activity"
    ]
    # Ratio columns stored as fractions (kept to 4 decimals so 0.0123 survives)
    ratio_columns = ["Profit_Margin", "Operating_Margin"]

    history = []

    for _, row in company.iterrows():
        record = {"year": int(row["Year"])}

        for col in amount_columns:
            if col in company.columns:
                value = pd.to_numeric(row[col], errors="coerce")
                record[col] = None if pd.isna(value) else round(float(value), 2)

        for col in ratio_columns:
            if col in company.columns:
                value = pd.to_numeric(row[col], errors="coerce")
                record[col] = None if pd.isna(value) else round(float(value), 4)

        history.append(record)

    latest = company.iloc[-1]
    previous = company.iloc[-2] if len(company) >= 2 else None

    growth = {}

    for col in ["Sales", "Net profit"]:
        if previous is not None and col in company.columns:
            old = pd.to_numeric(previous[col], errors="coerce")
            new = pd.to_numeric(latest[col], errors="coerce")

            if pd.notna(old) and pd.notna(new) and old != 0:
                growth[col] = round(((new - old) / abs(old)) * 100, 2)
            else:
                growth[col] = None
        else:
            growth[col] = None

    return {
        "company": company_name,
        "history": history,
        "latest_year": int(latest["Year"]),
        "year_over_year_growth_percent": growth
    }


def get_stability_analysis(company_name):
    result = fundamental_agent.analyze_company(company_name)
    metrics = result["financial_metrics"]

    debt_equity = metrics.get("Debt_to_Equity")
    interest_coverage = metrics.get("Interest_Coverage")
    operating_cash = metrics.get("Cash from Operating Activity")

    observations = []

    if debt_equity is not None:
        if debt_equity <= 0.5:
            observations.append("Relatively low debt-to-equity ratio.")
        elif debt_equity <= 1.5:
            observations.append("Moderate debt relative to equity.")
        else:
            observations.append("High debt relative to equity; monitor leverage.")

    if interest_coverage is not None:
        if interest_coverage < 1:
            observations.append("Operating earnings may be insufficient to cover interest.")
        elif interest_coverage < 2:
            observations.append("Limited interest coverage; monitor debt servicing.")
        else:
            observations.append("Interest coverage indicates capacity to service interest.")

    if operating_cash is not None:
        if operating_cash < 0:
            observations.append("Negative operating cash flow requires investigation.")
        else:
            observations.append("Operating activities generated positive cash flow.")

    return {
        "company": result["company"],
        "financial_year": result["financial_year"],
        "indicators": {
            "borrowings": metrics.get("Borrowings"),
            "debt_to_equity": debt_equity,
            "interest_coverage": interest_coverage,
            "cash_and_bank": metrics.get("Cash & Bank"),
            "operating_cash_flow": operating_cash
        },
        "observations": observations,
        "note": "Rule-based preliminary assessment, not a credit rating."
    }


# (min, max) plausible bounds. Adjust if your columns are scaled differently.
EXTREME_RULES = {
    "Debt_to_Equity": (0, 10),
    "Profit_Margin": (-1, 1),
    "Operating_Margin": (-1, 1),
    "ROE": (-2, 2),
    "ROA": (-1, 1),
}


def extreme_value_warnings(company_df):
    warnings = []

    for col, (low, high) in EXTREME_RULES.items():
        if col not in company_df.columns:
            continue

        values = pd.to_numeric(company_df[col], errors="coerce")
        mask = (values < low) | (values > high)

        for idx in company_df.index[mask.fillna(False)]:
            year = pd.to_numeric(company_df.at[idx, "Year"], errors="coerce")
            year_text = f"FY {int(year)}" if pd.notna(year) else "an unknown year"
            warnings.append(
                f"{col} = {values.at[idx]:.2f} in {year_text} looks extreme "
                "(possible data error or unusual year)."
            )

    return warnings


def get_data_quality(company_name):
    df = fundamental_agent.financial_df
    company = df[
        df["Company"].str.casefold() == company_name.strip().casefold()
    ].copy()

    if company.empty:
        raise ValueError(f"Company '{company_name}' was not found.")

    numeric = company.select_dtypes(include=[np.number])
    missing = company.isna().sum()
    missing_fields = {k: int(v) for k, v in missing[missing > 0].items()}

    non_finite = {}
    for col in numeric.columns:
        count = int((~np.isfinite(numeric[col].dropna())).sum())
        if count:
            non_finite[col] = count

    warnings = []

    for col in ["Sales", "Total Assets", "Net profit", "Borrowings"]:
        if col in company.columns and (company[col] < 0).any():
            warnings.append(f"Negative values detected in {col}.")

    if "Total Assets" in company.columns and "Total Liabilities" in company.columns:
        if not np.allclose(
            company["Total Assets"].fillna(0),
            company["Total Liabilities"].fillna(0)
        ):
            warnings.append("Total Assets and Total Liabilities differ in some records.")

    warnings.extend(extreme_value_warnings(company))

    return {
        "company": company_name,
        "records_checked": int(len(company)),
        "missing_values": missing_fields,
        "non_finite_values": non_finite,
        "warnings": warnings,
        "status": (
            "Review required"
            if missing_fields or non_finite or warnings
            else "No issues detected by basic checks"
        )
    }


# ---------------------------------------------------------------------------
# Complete report
# ---------------------------------------------------------------------------

@router.get("/report/{company_name}")
def complete_fundamental_report(company_name: str):
    try:
        analysis = fundamental_agent.analyze_company(company_name)
        canonical_name = analysis["company"]

        report = {
            "company": canonical_name,
            "analysis": analysis,  # overview, ML prediction, latest metrics
            "historical_performance": get_company_history(canonical_name),
            "financial_stability": get_stability_analysis(canonical_name),
            "data_quality": get_data_quality(canonical_name),
            # Kept so older frontend code that reads valuation_ratios still works.
            "valuation_ratios": {
                "ROE (dataset, latest FY)": (
                    f"{_pct(analysis['financial_metrics'].get('ROE'))}%"
                    if analysis["financial_metrics"].get("ROE") is not None
                    else "N/A"
                ),
                "P/E and P/B": "See current Yahoo Finance section",
            },
        }
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(error)}"
        )

    # Current market ratios from Yahoo Finance (never blocks the report)
    try:
        report["market_valuation"] = get_valuation(report["company"])
    except Exception as error:
        report["market_valuation"] = {"error": str(error)}

    return report


# ---------------------------------------------------------------------------
# Peer comparison with industry validation
# ---------------------------------------------------------------------------

PEER_METRICS = [
    ("Sales", "Sales", False),
    ("Net profit", "Net_Profit", False),
    ("Profit_Margin", "Profit_Margin_%", True),
    ("Operating_Margin", "Operating_Margin_%", True),
    ("ROE", "ROE_%", True),
    ("ROA", "ROA_%", True),
    ("Debt_to_Equity", "Debt_to_Equity", False),
    ("Interest_Coverage", "Interest_Coverage", False),
]


@router.get("/peer-compare/{company_name}")
def compare_companies(company_name: str, peer_name: str):
    try:
        first = fundamental_agent.analyze_company(company_name)
        second = fundamental_agent.analyze_company(peer_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Peer comparison failed: {str(error)}"
        )

    name_1 = first["company"]
    name_2 = second["company"]

    if name_1 == name_2:
        raise HTTPException(
            status_code=400,
            detail="Please choose a different company to compare with."
        )

    comparison = {}

    for source_key, label, is_ratio in PEER_METRICS:
        v1 = first["financial_metrics"].get(source_key)
        v2 = second["financial_metrics"].get(source_key)

        if is_ratio:
            v1, v2 = _pct(v1), _pct(v2)

        comparison[label] = {name_1: v1, name_2: v2}

    # Industry validation
    s1, i1 = _sector_info(name_1)
    s2, i2 = _sector_info(name_2)

    if not (s1 and s2):
        comparable = None
        warning = "Sector information could not be verified for one or both companies."
    elif s1 != s2:
        comparable = False
        warning = (
            f"{name_1} ({s1}) and {name_2} ({s2}) are in different sectors. "
            "Margins, debt levels and growth are not directly comparable."
        )
    elif i1 != i2:
        comparable = True
        warning = f"Same sector ({s1}) but different industries ({i1} vs {i2})."
    else:
        comparable = True
        warning = None

    return {
        "company_1": name_1,
        "company_2": name_2,
        "financial_years": {
            name_1: first["financial_year"],
            name_2: second["financial_year"],
        },
        "comparison": comparison,
        "comparable": comparable,
        "warning": warning,
        "sectors": {name_1: s1, name_2: s2},
        "note": (
            "Historical dataset values for each company's latest available "
            "financial year; the two years may differ. Ratios are shown in %."
        ),
    }