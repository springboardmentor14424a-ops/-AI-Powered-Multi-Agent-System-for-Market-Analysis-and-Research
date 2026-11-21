"""Quality checks for downloaded price history.

The checks only REPORT problems (and record what _clean already removed); they never
silently change numbers. Each check says how many rows it affects and gives examples.
"""
from datetime import date

import pandas as pd

MAX_GAP_DAYS = 7          # longer than a normal holiday stretch
EXTREME_MOVE = 0.30       # a >30% one-day close-to-close move is suspicious (split? bad tick?)
ZERO_VOLUME_SHARE = 0.20  # more than 20% of days with no volume is suspicious
STALE_DAYS = 10
EXAMPLES = 5


def _dates(mask: pd.Series) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in mask[mask].index[:EXAMPLES]]


def _check(id_, label, severity, count, detail, examples=None):
    return {
        "id": id_,
        "label": label,
        "severity": severity,
        "passed": count == 0,
        "count": int(count),
        "detail": detail if count else "No problems found.",
        "examples": examples or [],
    }


def validate_prices(frame: pd.DataFrame, cleaning: dict | None = None, today: date | None = None) -> dict:
    """Return {status, rows, first_date, last_date, checks[], flagged{date: reason}}."""
    cleaning = cleaning or {}
    today = today or date.today()
    o, h, l, c, v = (frame[k] for k in ("open", "high", "low", "close", "volume"))
    flagged: dict[str, str] = {}

    def flag(mask: pd.Series, reason: str):
        for d in mask[mask].index:
            flagged.setdefault(d.strftime("%Y-%m-%d"), reason)

    checks = []

    # 1. Duplicate dates (removed while loading; any left would also be caught here)
    removed = int(cleaning.get("duplicate_dates_removed", 0))
    left = int(frame.index.duplicated().sum())
    checks.append(
        _check(
            "duplicate_dates", "Duplicate dates", "warning", removed + left,
            f"{removed} duplicate date(s) were removed (the last row for a date was kept)"
            + (f"; {left} still present" if left else "") + ".",
        )
    )

    # 2. Missing values
    missing_cells = frame[["open", "high", "low", "close", "volume"]].isna()
    missing_rows = missing_cells.any(axis=1)
    dropped = int(cleaning.get("rows_without_close_removed", 0))
    flag(missing_rows, "missing value")
    checks.append(
        _check(
            "missing_values", "Missing values", "warning", int(missing_rows.sum()) + dropped,
            f"{int(missing_rows.sum())} row(s) have an empty open/high/low/volume cell; "
            f"{dropped} row(s) with no closing price were removed.",
            _dates(missing_rows),
        )
    )

    # 3. Inconsistent prices
    bad_range = (h < l)
    bad_envelope = (h < pd.concat([o, c], axis=1).max(axis=1)) | (l > pd.concat([o, c], axis=1).min(axis=1))
    non_positive = (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
    inconsistent = (bad_range | bad_envelope | non_positive).fillna(False)
    flag(non_positive.fillna(False), "price is zero or negative")
    flag(bad_range.fillna(False), "high is below low")
    flag(bad_envelope.fillna(False), "open/close outside the high-low range")
    checks.append(
        _check(
            "inconsistent_prices", "Inconsistent prices", "error", int(inconsistent.sum()),
            "High below low, open/close outside the day's high-low range, or a zero/negative price.",
            _dates(inconsistent),
        )
    )

    # 4. Volume
    negative_vol = (v < 0).fillna(False)
    flag(negative_vol, "negative volume")
    checks.append(
        _check("negative_volume", "Negative volume", "error", int(negative_vol.sum()),
               "Volume can never be below zero.", _dates(negative_vol))
    )
    zero_vol = (v == 0).fillna(False)
    share = float(zero_vol.mean()) if len(v) else 0.0
    many_zero = int(zero_vol.sum()) if share > ZERO_VOLUME_SHARE else 0
    checks.append(
        _check("zero_volume", "Days with no volume", "warning", many_zero,
               f"{share:.0%} of days report zero volume (some providers omit volume for indices).")
    )

    # 5. Gaps in the calendar
    gaps = frame.index.to_series().diff().dt.days
    big_gap = gaps > MAX_GAP_DAYS
    gap_examples = [
        f"{(d - pd.Timedelta(days=int(gaps[d]))):%Y-%m-%d} to {d:%Y-%m-%d}" for d in big_gap[big_gap].index[:EXAMPLES]
    ]
    checks.append(
        _check("date_gaps", "Gaps in the date range", "warning", int(big_gap.sum()),
               f"{int(big_gap.sum())} gap(s) longer than {MAX_GAP_DAYS} days between trading days.", gap_examples)
    )

    # 6. Extreme one-day moves
    move = c.pct_change().abs()
    extreme = (move > EXTREME_MOVE).fillna(False)
    flag(extreme, "extreme one-day move")
    checks.append(
        _check("extreme_moves", "Extreme one-day moves", "warning", int(extreme.sum()),
               f"Close changed by more than {EXTREME_MOVE:.0%} in a day (a split, a data error, or a real shock).",
               _dates(extreme))
    )

    # 7. Dates in the future / stale data
    future = pd.Series(frame.index.date > today, index=frame.index)
    flag(future, "date is in the future")
    checks.append(
        _check("future_dates", "Dates in the future", "error", int(future.sum()),
               "Price history must not contain dates after today.", _dates(future))
    )
    age = (today - frame.index[-1].date()).days if len(frame) else 0
    checks.append(
        _check("stale", "Data is up to date", "warning", 1 if age > STALE_DAYS else 0,
               f"Latest price is from {frame.index[-1]:%Y-%m-%d}, {age} days ago.")
    )

    failed = [x for x in checks if not x["passed"]]
    status = "errors" if any(x["severity"] == "error" for x in failed) else "warnings" if failed else "ok"
    return {
        "status": status,
        "rows": int(len(frame)),
        "first_date": frame.index[0].strftime("%Y-%m-%d") if len(frame) else None,
        "last_date": frame.index[-1].strftime("%Y-%m-%d") if len(frame) else None,
        "checks": checks,
        "flagged": flagged,
    }
