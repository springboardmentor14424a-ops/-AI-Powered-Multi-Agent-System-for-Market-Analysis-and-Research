import pandas as pd
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_FILE = Path.home() / "Downloads" / "archive-2" / "Stock_RELIANCE.xlsx"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
    / "reliance_cleaned.csv"
)

# Load dataset
df = pd.read_excel(INPUT_FILE)

print("Original dataset shape:", df.shape)

# Convert Date column to datetime
df["Date"] = pd.to_datetime(df["Date"])

# Remove duplicate rows
df = df.drop_duplicates()

# Sort data chronologically
df = df.sort_values("Date").reset_index(drop=True)

# Remove Trades column because it contains many missing values
df = df.drop(columns=["Trades"])

# Check missing values
print("\nMissing values after preprocessing:")
print(df.isnull().sum())

# Save cleaned dataset
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print("\nPreprocessing completed successfully!")
print("Cleaned dataset shape:", df.shape)
print("Saved to:", OUTPUT_FILE)
