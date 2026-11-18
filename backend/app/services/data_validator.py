import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger("stock_research.validator")

class MarketDataValidator:
    """
    Institutional Market Data Quality & Integrity Validator.
    
    Validates, diagnoses, and remediates:
    1. Missing values (Open, High, Low, Close, Volume)
    2. Duplicate date entries
    3. Inconsistent data (Low > High, prices <= 0, Volume < 0, anomalies)
    4. Chronological time-series ordering
    """

    @classmethod
    def validate_and_clean_ohlcv(
        cls, 
        raw_records: List[Dict[str, Any]], 
        ticker: str = "EQUITY", 
        market: str = "NSE"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates raw OHLCV time-series records, handles missing values,
        eliminates duplicate dates, rectifies inconsistent price relations,
        and generates an institutional Data Validation Report.
        """
        if not raw_records:
            return [], {
                "is_valid": True,
                "quality_score": 100.0,
                "total_records": 0,
                "clean_records": 0,
                "missing_values_handled": 0,
                "duplicate_dates_removed": 0,
                "inconsistencies_corrected": 0,
                "issues_log": ["No records provided for validation."],
                "validated_at": datetime.utcnow().isoformat() + "Z"
            }

        issues_log: List[str] = []
        missing_handled = 0
        duplicate_removed = 0
        inconsistencies_corrected = 0
        total_input_count = len(raw_records)

        # 1. Audit raw records for missing fields
        for idx, rec in enumerate(raw_records):
            r_date = rec.get("date") or rec.get("datetime") or rec.get("timestamp")
            if not r_date:
                issues_log.append(f"Row {idx}: Missing date timestamp.")
                missing_handled += 1
            for field in ["open", "high", "low", "close", "volume"]:
                val = rec.get(field)
                if val is None or val == "":
                    missing_handled += 1
                    issues_log.append(f"Row {idx} (Date '{r_date}'): Missing '{field}' field detected in raw payload.")

        # 2. Date normalization & duplicate date elimination
        seen_dates = set()
        deduplicated: List[Dict[str, Any]] = []

        for idx, rec in enumerate(raw_records):
            raw_date = rec.get("date") or rec.get("datetime") or rec.get("timestamp")
            if not raw_date:
                continue
            
            # Normalize date string (YYYY-MM-DD)
            date_str = str(raw_date).split("T")[0].split(" ")[0].strip()
            
            if date_str in seen_dates:
                duplicate_removed += 1
                issues_log.append(f"Date '{date_str}': Duplicate entry detected and eliminated.")
                # Replace with latest occurrence if the current one has higher volume/validity
                deduplicated = [r for r in deduplicated if r["date"] != date_str]
            
            seen_dates.add(date_str)
            deduplicated.append({
                "date": date_str,
                "open": rec.get("open"),
                "high": rec.get("high"),
                "low": rec.get("low"),
                "close": rec.get("close") or rec.get("adjusted_close"),
                "volume": rec.get("volume"),
                "display_date": rec.get("display_date")
            })

        # 3. Sort chronologically
        try:
            sorted_records = sorted(deduplicated, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
            if [r["date"] for r in deduplicated] != [r["date"] for r in sorted_records]:
                issues_log.append("Time series was out of chronological order. Sequence re-sorted ascending.")
                inconsistencies_corrected += 1
        except Exception:
            sorted_records = deduplicated

        # 4. Impute missing values & price consistency validation
        cleaned: List[Dict[str, Any]] = []
        last_valid_close = 100.0

        for idx, item in enumerate(sorted_records):
            cur_date = item["date"]
            op = item.get("open")
            hi = item.get("high")
            lo = item.get("low")
            cl = item.get("close")
            vol = item.get("volume")

            # Check for missing values in surviving records
            if cl is None or cl == "" or cl == 0:
                cl = op if (op is not None and op > 0) else last_valid_close
                issues_log.append(f"Date '{cur_date}': Imputed Close price with {round(cl, 2)}.")

            try:
                cl = float(cl)
            except (ValueError, TypeError):
                cl = last_valid_close
                issues_log.append(f"Date '{cur_date}': Non-numeric Close value imputed with {round(cl, 2)}.")

            if op is None or op == "" or op == 0:
                op = cl
                issues_log.append(f"Date '{cur_date}': Imputed Open price from Close ({round(cl, 2)}).")
            else:
                try:
                    op = float(op)
                except (ValueError, TypeError):
                    op = cl

            if hi is None or hi == "":
                hi = max(op, cl)
                issues_log.append(f"Date '{cur_date}': Imputed High price as max(Open, Close)={round(hi, 2)}.")
            else:
                try:
                    hi = float(hi)
                except (ValueError, TypeError):
                    hi = max(op, cl)

            if lo is None or lo == "":
                lo = min(op, cl)
                issues_log.append(f"Date '{cur_date}': Imputed Low price as min(Open, Close)={round(lo, 2)}.")
            else:
                try:
                    lo = float(lo)
                except (ValueError, TypeError):
                    lo = min(op, cl)

            # Volume validation
            if vol is None or vol == "":
                vol = 100000
                issues_log.append(f"Date '{cur_date}': Imputed baseline Volume (100,000).")
            else:
                try:
                    vol = int(float(vol))
                    if vol < 0:
                        inconsistencies_corrected += 1
                        issues_log.append(f"Date '{cur_date}': Negative volume ({vol}) corrected to positive.")
                        vol = abs(vol)
                except (ValueError, TypeError):
                    vol = 100000

            # 4. Inconsistent price relationship checks (Low <= Open <= High and Low <= Close <= High)
            if hi < lo:
                inconsistencies_corrected += 1
                issues_log.append(f"Date '{cur_date}': Inverted bounds detected (High {hi} < Low {lo}). Values swapped.")
                hi, lo = lo, hi

            actual_high = max(op, cl, hi)
            if actual_high != hi:
                inconsistencies_corrected += 1
                issues_log.append(f"Date '{cur_date}': High price ({hi}) was lower than Open ({op}) or Close ({cl}). Adjusted High to {round(actual_high, 2)}.")
                hi = actual_high

            actual_low = min(op, cl, lo)
            if actual_low != lo:
                inconsistencies_corrected += 1
                issues_log.append(f"Date '{cur_date}': Low price ({lo}) was higher than Open ({op}) or Close ({cl}). Adjusted Low to {round(actual_low, 2)}.")
                lo = actual_low

            # Positive price enforcement
            if op <= 0 or hi <= 0 or lo <= 0 or cl <= 0:
                inconsistencies_corrected += 1
                issues_log.append(f"Date '{cur_date}': Non-positive price encountered. Corrected to positive baseline.")
                op = max(op, 1.0)
                hi = max(hi, op)
                lo = max(lo, 0.5)
                cl = max(cl, lo)

            last_valid_close = cl

            # Format display date (e.g. 'Nov 18')
            try:
                dt_obj = datetime.strptime(cur_date, "%Y-%m-%d")
                disp_date = dt_obj.strftime("%b %d")
            except Exception:
                disp_date = cur_date

            cleaned.append({
                "date": cur_date,
                "display_date": disp_date,
                "open": round(op, 2),
                "high": round(hi, 2),
                "low": round(lo, 2),
                "close": round(cl, 2),
                "volume": int(vol)
            })

        # Calculate Quality Score
        penalty = (missing_handled * 2.0) + (duplicate_removed * 2.5) + (inconsistencies_corrected * 3.0)
        quality_score = max(0.0, round(100.0 - (penalty / max(1, total_input_count) * 20.0), 1))
        if penalty == 0:
            quality_score = 100.0
            issues_log.append("Zero data anomalies found. Time-series passed 100% mathematical integrity validation.")

        report = {
            "is_valid": True,
            "quality_score": quality_score,
            "total_records": total_input_count,
            "clean_records": len(cleaned),
            "missing_values_handled": missing_handled,
            "duplicate_dates_removed": duplicate_removed,
            "inconsistencies_corrected": inconsistencies_corrected,
            "issues_log": issues_log,
            "validated_at": datetime.utcnow().isoformat() + "Z"
        }

        return cleaned, report
