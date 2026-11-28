import os
from datetime import datetime
import pandas as pd

# Where the raw Kaggle files are, and where cleaned files will go
RAW_DIR = os.path.join("data", "kaggle_raw", "archive")
CLEAN_DIR = os.path.join("data", "kaggle_clean")
os.makedirs(CLEAN_DIR, exist_ok=True)

SOURCE = "Kaggle - NIFTY-50 Stock Market Data (2000 - 2021)"
PROCESSED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# These two files are not single-company price files, so we skip them
SKIP = {"NIFTY50_all.csv", "stock_metadata.csv"}
KEEP = ["Date", "Open", "High", "Low", "Close", "Volume"]

report = []

for file_name in sorted(os.listdir(RAW_DIR)):
    if not file_name.lower().endswith(".csv") or file_name in SKIP:
        continue

    symbol = file_name[:-4]  # the file name is the correct symbol
    df = pd.read_csv(os.path.join(RAW_DIR, file_name))
    rows_before = len(df)

    df = df[KEEP].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # 1. Missing values (empty date, price or volume)
    missing_rows = int(df.isna().any(axis=1).sum())
    df = df.dropna()

    # 2. Duplicate dates
    duplicate_rows = int(df.duplicated(subset="Date").sum())
    df = df.drop_duplicates(subset="Date", keep="first")

    # 3. Inconsistent data (impossible prices)
    bad = (
        (df["High"] < df["Low"])
        | (df["Open"] > df["High"]) | (df["Open"] < df["Low"])
        | (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
        | (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
        | (df["Volume"] < 0)
    )
    inconsistent_rows = int(bad.sum())
    df = df[~bad]

    # Add symbol, source and timestamp, then sort by date
    df.insert(0, "Symbol", symbol)
    df["Source"] = SOURCE
    df["ProcessedAt"] = PROCESSED_AT
    df = df.sort_values("Date")

    df.to_csv(os.path.join(CLEAN_DIR, file_name), index=False)

    report.append({
        "Symbol": symbol,
        "RowsBefore": rows_before,
        "MissingRemoved": missing_rows,
        "DuplicatesRemoved": duplicate_rows,
        "InconsistentRemoved": inconsistent_rows,
        "RowsAfter": len(df),
    })

pd.DataFrame(report).to_csv(os.path.join(CLEAN_DIR, "validation_report.csv"), index=False)
print("Done. Cleaned", len(report), "files.")
