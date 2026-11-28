
import pandas as pd
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

OUTPUT_FILE = DATA_DIR / "reliance_revenue_earnings_analysis.csv"

# --------------------------------------------------
# LOAD FINANCIAL DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE, index_col=0)

# Convert the financial statement into a yearly table
df = df.T

# Convert column names to dates
df.index = pd.to_datetime(df.index)

# Sort years from oldest to newest
df = df.sort_index()

print("=" * 60)
print("REVENUE & EARNINGS ANALYSIS")
print("=" * 60)

# --------------------------------------------------
# EXTRACT FINANCIAL METRICS
# --------------------------------------------------

required_metrics = [
    "Total Revenue",
    "Net Income"
]

for metric in required_metrics:
    if metric not in df.columns:
        raise ValueError(f"Missing financial metric: {metric}")

analysis = pd.DataFrame(index=df.index)

analysis["Revenue"] = df["Total Revenue"]
analysis["Net_Income"] = df["Net Income"]

# --------------------------------------------------
# REVENUE GROWTH
# --------------------------------------------------

analysis["Revenue_Growth_%"] = (
    analysis["Revenue"].pct_change() * 100
)

# --------------------------------------------------
# EARNINGS GROWTH
# --------------------------------------------------

analysis["Earnings_Growth_%"] = (
    analysis["Net_Income"].pct_change() * 100
)

# --------------------------------------------------
# TREND ANALYSIS
# --------------------------------------------------

analysis["Revenue_Trend"] = analysis["Revenue"].diff()

analysis["Earnings_Trend"] = analysis["Net_Income"].diff()

# --------------------------------------------------
# SAVE RESULTS
# --------------------------------------------------

analysis = analysis.reset_index()

analysis = analysis.rename(columns={"index": "Financial_Year"})

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

analysis.to_csv(OUTPUT_FILE, index=False)

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print("\nAnnual Revenue and Earnings:")

display_columns = [
    "Financial_Year",
    "Revenue",
    "Revenue_Growth_%",
    "Net_Income",
    "Earnings_Growth_%"
]

print(
    analysis[display_columns].to_string(index=False)
)

print("\n" + "=" * 60)
print("ANALYSIS SUMMARY")
print("=" * 60)

latest = analysis.iloc[-1]

print("\nLatest available financial period:", latest["Financial_Year"])

print("Revenue:", latest["Revenue"])

print("Net Income:", latest["Net_Income"])

print("Revenue Growth:", latest["Revenue_Growth_%"], "%")

print("Earnings Growth:", latest["Earnings_Growth_%"], "%")

# --------------------------------------------------
# SAVE COMPLETION
# --------------------------------------------------

print("\nAnalysis saved successfully!")

print("Output file:")
print(OUTPUT_FILE)

