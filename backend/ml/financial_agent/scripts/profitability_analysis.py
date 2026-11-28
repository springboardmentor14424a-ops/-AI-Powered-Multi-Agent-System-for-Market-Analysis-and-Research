
import pandas as pd
import numpy as np
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATA_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
)

INPUT_FILE = DATA_DIR / "reliance_annual_income_statement.csv"

OUTPUT_FILE = DATA_DIR / "reliance_profitability_analysis.csv"

# --------------------------------------------------
# LOAD FINANCIAL DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE, index_col=0)

# Convert columns into rows representing financial years
df = df.T

# Convert financial year index to datetime
df.index = pd.to_datetime(df.index)

# Arrange years from oldest to newest
df = df.sort_index()

print("=" * 60)
print("PROFITABILITY ANALYSIS")
print("=" * 60)

# --------------------------------------------------
# CHECK REQUIRED METRICS
# --------------------------------------------------

required_metrics = [
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "Net Income",
    "EBITDA"
]

for metric in required_metrics:
    if metric not in df.columns:
        raise ValueError(f"Missing financial metric: {metric}")

# --------------------------------------------------
# EXTRACT FINANCIAL DATA
# --------------------------------------------------

analysis = pd.DataFrame(index=df.index)

analysis["Revenue"] = df["Total Revenue"]
analysis["Gross_Profit"] = df["Gross Profit"]
analysis["Operating_Income"] = df["Operating Income"]
analysis["Net_Income"] = df["Net Income"]
analysis["EBITDA"] = df["EBITDA"]

# --------------------------------------------------
# CALCULATE PROFITABILITY MARGINS
# --------------------------------------------------

# Gross Profit Margin
analysis["Gross_Profit_Margin_%"] = (
    analysis["Gross_Profit"] / analysis["Revenue"] * 100
)

# Operating Profit Margin
analysis["Operating_Margin_%"] = (
    analysis["Operating_Income"] / analysis["Revenue"] * 100
)

# Net Profit Margin
analysis["Net_Profit_Margin_%"] = (
    analysis["Net_Income"] / analysis["Revenue"] * 100
)

# EBITDA Margin
analysis["EBITDA_Margin_%"] = (
    analysis["EBITDA"] / analysis["Revenue"] * 100
)

# --------------------------------------------------
# PROFITABILITY TREND ANALYSIS
# --------------------------------------------------

analysis["Gross_Margin_Change"] = (
    analysis["Gross_Profit_Margin_%"].diff()
)

analysis["Operating_Margin_Change"] = (
    analysis["Operating_Margin_%"].diff()
)

analysis["Net_Margin_Change"] = (
    analysis["Net_Profit_Margin_%"].diff()
)

# --------------------------------------------------
# PROFITABILITY STATUS
# --------------------------------------------------

def determine_trend(value):

    if pd.isna(value):
        return "Insufficient Data"

    elif value > 0:
        return "Improving"

    elif value < 0:
        return "Declining"

    else:
        return "Stable"


analysis["Gross_Margin_Status"] = (
    analysis["Gross_Margin_Change"].apply(determine_trend)
)

analysis["Operating_Margin_Status"] = (
    analysis["Operating_Margin_Change"].apply(determine_trend)
)

analysis["Net_Margin_Status"] = (
    analysis["Net_Margin_Change"].apply(determine_trend)
)

# --------------------------------------------------
# SAVE RESULTS
# --------------------------------------------------

analysis = analysis.reset_index()

analysis = analysis.rename(
    columns={"index": "Financial_Year"}
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

analysis.to_csv(OUTPUT_FILE, index=False)

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\nAnnual Profitability Analysis:\n")

display_columns = [
    "Financial_Year",
    "Gross_Profit_Margin_%",
    "Operating_Margin_%",
    "Net_Profit_Margin_%",
    "EBITDA_Margin_%"
]

print(
    analysis[display_columns].to_string(index=False)
)

# --------------------------------------------------
# LATEST YEAR SUMMARY
# --------------------------------------------------

latest = analysis.iloc[-1]

print("\n" + "=" * 60)
print("LATEST PROFITABILITY SUMMARY")
print("=" * 60)

print("\nFinancial Year:", latest["Financial_Year"])

print(
    "Gross Profit Margin:",
    round(latest["Gross_Profit_Margin_%"], 2),
    "%"
)

print(
    "Operating Margin:",
    round(latest["Operating_Margin_%"], 2),
    "%"
)

print(
    "Net Profit Margin:",
    round(latest["Net_Profit_Margin_%"], 2),
    "%"
)

print(
    "EBITDA Margin:",
    round(latest["EBITDA_Margin_%"], 2),
    "%"
)

# --------------------------------------------------
# TREND SUMMARY
# --------------------------------------------------

print("\nMargin Trends:")

print("Gross Margin:", latest["Gross_Margin_Status"])

print("Operating Margin:", latest["Operating_Margin_Status"])

print("Net Margin:", latest["Net_Margin_Status"])

# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 60)
print("PROFITABILITY ANALYSIS COMPLETED!")
print("=" * 60)

print("\nSaved to:")
print(OUTPUT_FILE)

