import pandas as pd
import numpy as np
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
    / "reliance_cleaned.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
    / "reliance_features.csv"
)

# Load cleaned data
df = pd.read_csv(INPUT_FILE, parse_dates=["Date"])

# Sort chronologically
df = df.sort_values("Date").reset_index(drop=True)

# -----------------------------
# Feature Engineering
# -----------------------------

# Daily percentage return
df["Daily_Return"] = df["Close"].pct_change()

# Moving averages
df["MA_5"] = df["Close"].rolling(window=5).mean()
df["MA_10"] = df["Close"].rolling(window=10).mean()
df["MA_20"] = df["Close"].rolling(window=20).mean()

# Price relative to moving averages
df["Close_MA5_Ratio"] = df["Close"] / df["MA_5"]
df["Close_MA10_Ratio"] = df["Close"] / df["MA_10"]
df["Close_MA20_Ratio"] = df["Close"] / df["MA_20"]

# 5-day rolling volatility
df["Volatility_5"] = df["Daily_Return"].rolling(window=5).std()

# Daily price range
df["Price_Range"] = df["High"] - df["Low"]

# Open-to-close percentage movement
df["Intraday_Return"] = (df["Close"] - df["Open"]) / df["Open"]

# Volume percentage change
df["Volume_Change"] = df["Volume"].pct_change()

# -----------------------------
# Target creation
# -----------------------------

# 1 = next day's closing price is higher
# 0 = next day's closing price is not higher
df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

# Last row has no next-day closing price, so remove it
df = df.iloc[:-1]

# Remove rows where rolling features are not yet available
df = df.dropna().reset_index(drop=True)

# Remove infinite values if any
df = df.replace([np.inf, -np.inf], np.nan).dropna()

# Save features dataset
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

# -----------------------------
# Results
# -----------------------------

print("Feature engineering completed!")
print("\nDataset shape:", df.shape)

print("\nFeatures created:")
print(df.columns.tolist())

print("\nTarget distribution:")
print(df["Target"].value_counts())

print("\nTarget percentages:")
print(df["Target"].value_counts(normalize=True) * 100)

print("\nSaved to:")
print(OUTPUT_FILE)

