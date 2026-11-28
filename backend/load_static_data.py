import os
from datetime import datetime

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

import models
from database import Base, engine

RAW_DIR = os.path.join("data", "kaggle_raw", "archive")
CLEAN_DIR = os.path.join("data", "kaggle_clean")
SOURCE = "Kaggle - NIFTY-50 Stock Market Data (2000 - 2021)"
SOURCE_URL = "https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data"

Base.metadata.create_all(bind=engine)  # creates the two new tables

with Session(engine) as db:
    # ---- 1. Company profiles from stock_metadata.csv ----
    # The file has 5 columns but only 4 headings, so we give correct names ourselves.
    meta = pd.read_csv(
        os.path.join(RAW_DIR, "stock_metadata.csv"),
        header=None, skiprows=1,
        names=["company_name", "industry", "symbol", "series", "isin"],
    )
    existing = set(db.scalars(select(models.StaticCompany.symbol)).all())
    companies_added = 0
    for row in meta.itertuples():
        symbol = str(row.symbol).strip()
        if symbol in existing:
            continue
        db.add(models.StaticCompany(
            symbol=symbol,
            company_name=str(row.company_name).strip(),
            industry=str(row.industry).strip(),
            isin=str(row.isin).strip(),
        ))
        companies_added += 1
    db.commit()

    # ---- 2. Cleaned prices ----
    loaded = set(db.scalars(select(models.StaticPrice.symbol).distinct()).all())
    prices_added = 0
    for file_name in sorted(os.listdir(CLEAN_DIR)):
        if not file_name.endswith(".csv") or file_name == "validation_report.csv":
            continue
        symbol = file_name[:-4]
        if symbol in loaded:
            continue
        df = pd.read_csv(os.path.join(CLEAN_DIR, file_name))
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        processed_at = datetime.strptime(df["ProcessedAt"].iloc[0], "%Y-%m-%d %H:%M:%S")
        records = [
            dict(
                symbol=symbol, trade_date=r.Date,
                open=float(r.Open), high=float(r.High), low=float(r.Low), close=float(r.Close),
                volume=int(r.Volume), source=r.Source, processed_at=processed_at,
            )
            for r in df.itertuples()
        ]
        db.execute(insert(models.StaticPrice), records)
        db.commit()
        prices_added += len(records)
        print("Loaded", symbol, len(records), "rows")

    # ---- 3. Source record (same table the Yahoo Finance sources use) ----
    title = "Static dataset: " + SOURCE
    if not db.scalar(select(models.SourceDocument).where(models.SourceDocument.title == title)):
        db.add(models.SourceDocument(
            source_type="static_dataset", title=title, source_url=SOURCE_URL,
        ))
        db.commit()

    # ---- 4. Consistency check ----
    meta_symbols = set(db.scalars(select(models.StaticCompany.symbol)).all())
    price_symbols = set(db.scalars(select(models.StaticPrice.symbol).distinct()).all())
    print("Companies added:", companies_added, "| Price rows added:", prices_added)
    print("In prices but not in company list:", sorted(price_symbols - meta_symbols))
    print("In company list but not in prices:", sorted(meta_symbols - price_symbols))
    