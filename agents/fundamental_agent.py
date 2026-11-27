from datetime import datetime, timezone
import os
import pandas as pd
import yfinance as yf


DEFAULT_DATA_DIR = r"C:\Users\sanst_5a1e4f1\Downloads\archive (2)"


class FundamentalAnalysisAgent:
    """Fundamental analysis agent covering all 7 capabilities + synthesized takeaway."""

    def __init__(
        self,
        name: str = "FundamentalAnalysisAgent",
        data_dir: str = DEFAULT_DATA_DIR,
        max_peers: int = 8,
    ):
        self.name = name
        self.data_dir = data_dir
        self.max_peers = max_peers

    @staticmethod
    def normalize_symbol(raw_ticker: str) -> str:
        symbol = raw_ticker.strip().upper()
        for suffix in (".NS", ".BO"):
            if symbol.endswith(suffix):
                symbol = symbol[: -len(suffix)]
        return symbol.removeprefix("STOCK_")

    @staticmethod
    def format_yf_symbol(symbol: str, market: str | None) -> str:
        mkt = (market or "").strip().upper()
        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            return symbol
        if "NSE" in mkt:
            return f"{symbol}.NS"
        if "BSE" in mkt:
            return f"{symbol}.BO"
        return symbol

    @staticmethod
    def _safe_float(val) -> float | None:
        if val is None or pd.isna(val):
            return None
        try:
            f = float(val)
            return None if pd.isna(f) else f
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _pct_change(current: float | None, previous: float | None) -> float | None:
        if current is None or previous is None or previous == 0:
            return None
        return round(((current - previous) / abs(previous)) * 100, 2)

    @staticmethod
    def _normalize_deliverable(val: float | None) -> float | None:
        if val is None:
            return None
        return round(val * 100, 2) if val <= 1.0 else round(val, 2)

    @staticmethod
    def _pct_from_ratio(val: float | None) -> float | None:
        if val is None:
            return None
        return round(val * 100, 2) if abs(val) <= 2.0 else round(val, 2)

    def _load_symbol_df(self, symbol: str, market: str | None = None) -> tuple[pd.DataFrame, str, bool]:
        """Returns (df, source_ref, is_static)."""
        if os.path.isdir(self.data_dir):
            direct_file = os.path.join(self.data_dir, f"Stock_{symbol}.xlsx")
            if os.path.isfile(direct_file):
                df = pd.read_excel(direct_file)
                source_ref = os.path.basename(direct_file)
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
                return df, source_ref, True

            frames = []
            for fname in sorted(os.listdir(self.data_dir)):
                if fname.endswith(".xlsx") and not fname.startswith("Index_"):
                    fpath = os.path.join(self.data_dir, fname)
                    try:
                        temp = pd.read_excel(fpath)
                        sym_col = "Symbol" if "Symbol" in temp.columns else ("Ticker" if "Ticker" in temp.columns else None)
                        if sym_col:
                            matched = temp[temp[sym_col].astype(str).str.strip().str.upper() == symbol]
                            if not matched.empty:
                                frames.append(matched)
                    except Exception:
                        continue
            if frames:
                df = pd.concat(frames, ignore_index=True)
                if "Date" in df.columns:
                    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
                return df, f"{os.path.basename(self.data_dir)} ({symbol})", True

        # Fallback to live yfinance history if symbol is not in static folder (e.g., AAPL)
        yf_sym = self.format_yf_symbol(symbol, market)
        hist = yf.Ticker(yf_sym).history(period="1y")
        if hist is None or hist.empty:
            raise ValueError(f"No static or live market records found for symbol '{symbol}'.")
        df = hist.reset_index()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        return df, f"Yahoo Finance ({yf_sym})", False

    def _fetch_live_fundamentals(self, symbol: str, market: str | None) -> dict:
        """Pulls statement & valuation metrics from yfinance to backfill missing static columns."""
        yf_sym = self.format_yf_symbol(symbol, market)
        data = {
            "company_name": symbol,
            "latest_revenue": None,
            "previous_revenue": None,
            "latest_net_income": None,
            "previous_net_income": None,
            "gross_margin_pct": None,
            "operating_margin_pct": None,
            "net_margin_pct": None,
            "total_debt": None,
            "cash_and_equivalents": None,
            "stockholders_equity": None,
            "debt_to_equity": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "roe_pct": None,
            "has_live_statements": False,
        }
        try:
            stock = yf.Ticker(yf_sym)
            info = stock.info or {}

            data["company_name"] = info.get("longName") or info.get("shortName") or symbol
            data["latest_revenue"] = self._safe_float(info.get("totalRevenue"))
            data["latest_net_income"] = self._safe_float(info.get("netIncomeToCommon"))
            data["gross_margin_pct"] = self._pct_from_ratio(self._safe_float(info.get("grossMargins")))
            data["operating_margin_pct"] = self._pct_from_ratio(self._safe_float(info.get("operatingMargins")))
            data["net_margin_pct"] = self._pct_from_ratio(self._safe_float(info.get("profitMargins")))
            data["total_debt"] = self._safe_float(info.get("totalDebt"))
            data["cash_and_equivalents"] = self._safe_float(info.get("totalCash"))
            data["pe_ratio"] = self._safe_float(info.get("trailingPE") or info.get("forwardPE"))
            data["pb_ratio"] = self._safe_float(info.get("priceToBook"))
            data["roe_pct"] = self._pct_from_ratio(self._safe_float(info.get("returnOnEquity")))

            raw_dte = self._safe_float(info.get("debtToEquity"))
            if raw_dte is not None:
                # yfinance debtToEquity is typically expressed as a percentage (e.g. 24.5 -> 0.25x)
                data["debt_to_equity"] = round(raw_dte / 100.0, 2) if raw_dte > 5 else round(raw_dte, 2)

            # Pull multi-period income statement for YoY revenue & net income comparison
            fin_df = stock.income_stmt
            if fin_df is None or fin_df.empty:
                fin_df = stock.financials
            if fin_df is not None and not fin_df.empty:
                if "Total Revenue" in fin_df.index:
                    rev_vals = [self._safe_float(v) for v in fin_df.loc["Total Revenue"].dropna().tolist()]
                    if len(rev_vals) >= 1:
                        data["latest_revenue"] = rev_vals[0]
                    if len(rev_vals) >= 2:
                        data["previous_revenue"] = rev_vals[1]
                if "Net Income" in fin_df.index:
                    ni_vals = [self._safe_float(v) for v in fin_df.loc["Net Income"].dropna().tolist()]
                    if len(ni_vals) >= 1:
                        data["latest_net_income"] = ni_vals[0]
                    if len(ni_vals) >= 2:
                        data["previous_net_income"] = ni_vals[1]

            # Pull balance sheet for Stockholders Equity if available
            bs_df = stock.balance_sheet
            if bs_df is not None and not bs_df.empty:
                for eq_label in ("Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"):
                    if eq_label in bs_df.index:
                        eq_vals = [self._safe_float(v) for v in bs_df.loc[eq_label].dropna().tolist()]
                        if eq_vals:
                            data["stockholders_equity"] = eq_vals[0]
                            break
                if data["debt_to_equity"] is None and data["total_debt"] is not None and data["stockholders_equity"]:
                    data["debt_to_equity"] = round(data["total_debt"] / data["stockholders_equity"], 2)

            if any(
                data[k] is not None
                for k in ("latest_revenue", "latest_net_income", "net_margin_pct", "total_debt", "pe_ratio")
            ):
                data["has_live_statements"] = True
        except Exception as exc:
            print(f"Live fundamental backfill warning for {yf_sym}: {exc}")

        return data

    def analyze_revenue_and_earnings(self, latest_row: pd.Series, prev_row: pd.Series | None, live: dict) -> dict:
        latest_rev = live.get("latest_revenue")
        prev_rev = live.get("previous_revenue")
        rev_growth = self._pct_change(latest_rev, prev_rev)

        latest_ni = live.get("latest_net_income")
        prev_ni = live.get("previous_net_income")
        ni_growth = self._pct_change(latest_ni, prev_ni)

        latest_turnover = self._safe_float(latest_row.get("Turnover"))
        prev_turnover = self._safe_float(prev_row.get("Turnover")) if prev_row is not None else None
        turnover_growth_pct = self._pct_change(latest_turnover, prev_turnover)

        if latest_rev is not None or latest_ni is not None:
            parts = []
            if latest_rev is not None:
                parts.append(
                    f"Latest annual Revenue is {latest_rev:,.0f}"
                    + (f" ({rev_growth:+.2f}% YoY)" if rev_growth is not None else "")
                )
            if latest_ni is not None:
                parts.append(
                    f"Net Income is {latest_ni:,.0f}"
                    + (f" ({ni_growth:+.2f}% YoY)" if ni_growth is not None else "")
                )
            summary = "; ".join(parts) + "."
        elif latest_turnover is not None:
            summary = (
                f"Static dataset has no income statement revenue/net income; "
                f"latest Turnover is {latest_turnover:,.2f}"
                + (f" ({turnover_growth_pct:+.2f}% vs prior row)." if turnover_growth_pct is not None else ".")
            )
        else:
            summary = "Income statement revenue and earnings are unavailable for this symbol."

        return {
            "latest_revenue": latest_rev,
            "previous_revenue": prev_rev,
            "revenue_growth_pct": rev_growth,
            "latest_net_income": latest_ni,
            "previous_net_income": prev_ni,
            "earnings_growth_pct": ni_growth,
            "turnover_proxy": {
                "latest_turnover": latest_turnover,
                "previous_turnover": prev_turnover,
                "turnover_change_pct": turnover_growth_pct,
            },
            "summary": summary,
        }

    def analyze_profitability(self, latest_row: pd.Series, live: dict) -> dict:
        close_val = self._safe_float(latest_row.get("Close"))
        prev_close_val = self._safe_float(latest_row.get("Prev Close"))
        intraday_change_pct = self._pct_change(close_val, prev_close_val)

        gm = live.get("gross_margin_pct")
        om = live.get("operating_margin_pct")
        nm = live.get("net_margin_pct")

        if any(m is not None for m in (gm, om, nm)):
            parts = []
            if gm is not None:
                parts.append(f"Gross Margin {gm:.2f}%")
            if om is not None:
                parts.append(f"Operating Margin {om:.2f}%")
            if nm is not None:
                parts.append(f"Net Profit Margin {nm:.2f}%")
            summary = "Profitability margins (backfilled from financial statements): " + ", ".join(parts) + "."
        else:
            summary = (
                "Profitability margins (gross/operating/net) unavailable"
                + (f"; latest Close vs Prev Close is {intraday_change_pct:+.2f}%." if intraday_change_pct is not None else ".")
            )

        return {
            "gross_margin_pct": gm,
            "operating_margin_pct": om,
            "net_margin_pct": nm,
            "price_change_vs_prev_close_pct": intraday_change_pct,
            "summary": summary,
        }

    def analyze_debt_and_stability(self, latest_row: pd.Series, live: dict) -> dict:
        deliverable_pct = self._normalize_deliverable(self._safe_float(latest_row.get("%Deliverble")))
        vwap_val = self._safe_float(latest_row.get("VWAP"))
        close_val = self._safe_float(latest_row.get("Close"))

        total_debt = live.get("total_debt")
        cash = live.get("cash_and_equivalents")
        equity = live.get("stockholders_equity")
        dte = live.get("debt_to_equity")
        cash_to_debt = round(cash / total_debt, 2) if (cash is not None and total_debt and total_debt > 0) else None

        if dte is not None:
            if dte < 0.5:
                stability = "Conservative / Low Leverage"
            elif dte <= 1.5:
                stability = "Moderate Leverage"
            else:
                stability = "High Leverage"
            summary = (
                f"Debt-to-Equity stands at {dte:.2f}x ({stability})"
                + (f", with Cash/Debt coverage of {cash_to_debt:.2f}x." if cash_to_debt is not None else ".")
            )
        elif total_debt is not None or cash is not None:
            stability = "Partial Balance Sheet Available"
            summary = (
                f"Total Debt: {total_debt:,.0f}, Cash & Equivalents: {cash:,.0f}."
                if (total_debt is not None and cash is not None)
                else "Partial balance sheet figures retrieved from live statements."
            )
        else:
            stability = "Balance sheet debt/equity unavailable"
            summary = (
                "Balance sheet debt/equity metrics are unavailable"
                + (f"; latest %Deliverble is {deliverable_pct:.2f}%." if deliverable_pct is not None else ".")
            )

        return {
            "total_debt": total_debt,
            "cash_and_equivalents": cash,
            "stockholders_equity": equity,
            "debt_to_equity": dte,
            "cash_to_debt": cash_to_debt,
            "stability_assessment": stability,
            "trading_stability_context": {
                "close": close_val,
                "vwap": vwap_val,
                "deliverable_pct": deliverable_pct,
            },
            "summary": summary,
        }

    def analyze_valuation_and_ratios(self, live: dict) -> dict:
        pe = live.get("pe_ratio")
        pb = live.get("pb_ratio")
        roe = live.get("roe_pct")

        if any(v is not None for v in (pe, pb, roe)):
            parts = []
            if pe is not None:
                parts.append(f"P/E: {pe:.2f}x")
            if pb is not None:
                parts.append(f"P/B: {pb:.2f}x")
            if roe is not None:
                parts.append(f"ROE: {roe:.2f}%")
            summary = "Valuation & return multiples: " + ", ".join(parts) + "."
        else:
            summary = "P/E, P/B, and ROE valuation fields are unavailable for this symbol."

        return {
            "pe_ratio": round(pe, 2) if pe is not None else None,
            "pb_ratio": round(pb, 2) if pb is not None else None,
            "roe_pct": roe,
            "summary": summary,
        }

    def analyze_historical_comparison(self, df: pd.DataFrame) -> dict:
        close_series = pd.to_numeric(df["Close"], errors="coerce").dropna() if "Close" in df.columns else pd.Series(dtype=float)
        turnover_series = pd.to_numeric(df["Turnover"], errors="coerce").dropna() if "Turnover" in df.columns else pd.Series(dtype=float)
        deliverable_series = (
            pd.to_numeric(df["%Deliverble"], errors="coerce").dropna().apply(self._normalize_deliverable).dropna()
            if "%Deliverble" in df.columns
            else pd.Series(dtype=float)
        )

        latest_close = self._safe_float(close_series.iloc[-1]) if not close_series.empty else None
        lookback_20_close = self._safe_float(close_series.tail(20).mean()) if not close_series.empty else None
        all_time_avg_close = self._safe_float(close_series.mean()) if not close_series.empty else None
        vs_20d_avg_pct = self._pct_change(latest_close, lookback_20_close)
        vs_all_time_avg_pct = self._pct_change(latest_close, all_time_avg_close)

        latest_turnover = self._safe_float(turnover_series.iloc[-1]) if not turnover_series.empty else None
        avg_20d_turnover = self._safe_float(turnover_series.tail(20).mean()) if not turnover_series.empty else None
        turnover_vs_20d_pct = self._pct_change(latest_turnover, avg_20d_turnover)

        latest_deliv = self._safe_float(deliverable_series.iloc[-1]) if not deliverable_series.empty else None
        avg_20d_deliv = self._safe_float(deliverable_series.tail(20).mean()) if not deliverable_series.empty else None

        return {
            "records_analyzed": int(len(df)),
            "date_range": {
                "start": df["Date"].min().strftime("%Y-%m-%d") if "Date" in df.columns and not df.empty else None,
                "end": df["Date"].max().strftime("%Y-%m-%d") if "Date" in df.columns and not df.empty else None,
            },
            "close_comparison": {
                "latest_close": latest_close,
                "avg_20d_close": round(lookback_20_close, 2) if lookback_20_close is not None else None,
                "vs_20d_avg_pct": vs_20d_avg_pct,
                "all_time_avg_close": round(all_time_avg_close, 2) if all_time_avg_close is not None else None,
                "vs_all_time_avg_pct": vs_all_time_avg_pct,
            },
            "turnover_comparison": {
                "latest_turnover": latest_turnover,
                "avg_20d_turnover": round(avg_20d_turnover, 2) if avg_20d_turnover is not None else None,
                "vs_20d_avg_pct": turnover_vs_20d_pct,
            },
            "deliverable_comparison": {
                "latest_deliverable_pct": latest_deliv,
                "avg_20d_deliverable_pct": round(avg_20d_deliv, 2) if avg_20d_deliv is not None else None,
            },
            "summary": (
                f"Over {len(df)} historical records, latest Close is "
                f"{f'{vs_20d_avg_pct:+.2f}% vs 20-period avg' if vs_20d_avg_pct is not None else 'N/A'}"
                f" and {f'{vs_all_time_avg_pct:+.2f}% vs historical avg' if vs_all_time_avg_pct is not None else 'N/A'}."
            ),
        }

    def analyze_peer_comparison(self, symbol: str) -> dict:
        if not os.path.isdir(self.data_dir):
            return {
                "available": False,
                "peers": [],
                "summary": "Peer comparison unavailable because static dataset directory was not found.",
            }

        peer_files = [
            f for f in sorted(os.listdir(self.data_dir))
            if f.startswith("Stock_") and f.endswith(".xlsx")
        ]

        peers = []
        for fname in peer_files:
            peer_sym = self.normalize_symbol(fname[len("Stock_"):-len(".xlsx")])
            if peer_sym == symbol:
                continue
            try:
                pdf = pd.read_excel(os.path.join(self.data_dir, fname))
                if pdf.empty:
                    continue
                if "Date" in pdf.columns:
                    pdf["Date"] = pd.to_datetime(pdf["Date"], errors="coerce")
                    pdf = pdf.dropna(subset=["Date"]).sort_values("Date")
                row = pdf.iloc[-1]
                close_val = self._safe_float(row.get("Close"))
                prev_close_val = self._safe_float(row.get("Prev Close"))
                peers.append({
                    "peer_symbol": peer_sym,
                    "as_of_date": row["Date"].strftime("%Y-%m-%d") if "Date" in pdf.columns and pd.notna(row.get("Date")) else None,
                    "latest_close": close_val,
                    "change_vs_prev_close_pct": self._pct_change(close_val, prev_close_val),
                    "latest_turnover": self._safe_float(row.get("Turnover")),
                    "deliverable_pct": self._normalize_deliverable(self._safe_float(row.get("%Deliverble"))),
                })
                if len(peers) >= self.max_peers:
                    break
            except Exception:
                continue

        peer_closes = [p["latest_close"] for p in peers if p["latest_close"] is not None]
        peer_avg_close = round(sum(peer_closes) / len(peer_closes), 2) if peer_closes else None

        return {
            "available": len(peers) > 0,
            "peer_count": len(peers),
            "peer_avg_latest_close": peer_avg_close,
            "peers": peers,
            "summary": (
                f"Compared against {len(peers)} peer symbols from static dataset (peer avg latest Close: {peer_avg_close:,.2f})."
                if peers and peer_avg_close is not None
                else "No comparable peer symbols found in the static dataset."
            ),
        }

    def identify_missing_or_inconsistent_data(self, df: pd.DataFrame, live: dict, is_static: bool) -> dict:
        field_checks = [
            ("Revenue", live.get("latest_revenue")),
            ("Net Income", live.get("latest_net_income")),
            ("Gross Margin", live.get("gross_margin_pct")),
            ("Operating Margin", live.get("operating_margin_pct")),
            ("Net Margin", live.get("net_margin_pct")),
            ("Total Debt", live.get("total_debt")),
            ("Cash & Equivalents", live.get("cash_and_equivalents")),
            ("Stockholders Equity", live.get("stockholders_equity")),
            ("P/E Ratio", live.get("pe_ratio")),
            ("P/B Ratio", live.get("pb_ratio")),
            ("ROE", live.get("roe_pct")),
        ]
        missing_fundamental_fields = [label for label, val in field_checks if val is None]

        column_null_counts = {
            col: int(df[col].isna().sum())
            for col in df.columns
            if int(df[col].isna().sum()) > 0
        }

        inconsistent_rows = 0
        if {"High", "Low"}.issubset(df.columns):
            high_s = pd.to_numeric(df["High"], errors="coerce")
            low_s = pd.to_numeric(df["Low"], errors="coerce")
            inconsistent_rows += int((high_s < low_s).fillna(False).sum())

        if {"Close", "High", "Low"}.issubset(df.columns):
            close_s = pd.to_numeric(df["Close"], errors="coerce")
            high_s = pd.to_numeric(df["High"], errors="coerce")
            low_s = pd.to_numeric(df["Low"], errors="coerce")
            outside_bounds = ((close_s > high_s) | (close_s < low_s)).fillna(False)
            inconsistent_rows += int(outside_bounds.sum())

        for col in ("Volume", "Turnover"):
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                inconsistent_rows += int((s < 0).fillna(False).sum())

        issues = []
        if is_static and live.get("has_live_statements"):
            issues.append(
                "Static OHLCV dataset lacks accounting columns; financial statement & valuation ratios were backfilled from live Yahoo Finance statements."
            )
        if missing_fundamental_fields:
            issues.append(
                f"{len(missing_fundamental_fields)} accounting/valuation fields remain unavailable ({', '.join(missing_fundamental_fields)})."
            )
        if column_null_counts:
            null_summary = ", ".join(f"{k}: {v} nulls" for k, v in column_null_counts.items())
            issues.append(f"Missing column values detected ({null_summary}).")
        if inconsistent_rows > 0:
            issues.append(f"Detected {inconsistent_rows} row-level price/volume/bound inconsistencies.")
        if not issues:
            issues.append("No missing or inconsistent data detected across evaluated fields.")

        return {
            "has_issues": bool(missing_fundamental_fields or column_null_counts or inconsistent_rows > 0),
            "missing_fundamental_fields": missing_fundamental_fields,
            "column_null_counts": column_null_counts,
            "inconsistent_row_count": inconsistent_rows,
            "issues": issues,
            "summary": " ".join(issues),
        }

    def build_investment_takeaway(
        self,
        symbol: str,
        historical: dict,
        profitability: dict,
        debt: dict,
        valuation: dict,
        data_quality: dict,
    ) -> dict:
        vs_20d = historical.get("close_comparison", {}).get("vs_20d_avg_pct")
        vs_all = historical.get("close_comparison", {}).get("vs_all_time_avg_pct")
        deliv_pct = historical.get("deliverable_comparison", {}).get("latest_deliverable_pct")
        net_margin = profitability.get("net_margin_pct")
        dte = debt.get("debt_to_equity")
        roe = valuation.get("roe_pct")

        score = 0
        reasons = []

        if net_margin is not None:
            if net_margin >= 12:
                score += 1
                reasons.append(f"healthy net margin ({net_margin:.1f}%)")
            elif net_margin < 5:
                score -= 1
                reasons.append(f"thin net margin ({net_margin:.1f}%)")

        if roe is not None and roe >= 15:
            score += 1
            reasons.append(f"strong ROE ({roe:.1f}%)")

        if dte is not None:
            if dte < 0.5:
                score += 1
                reasons.append(f"low leverage (D/E {dte:.2f}x)")
            elif dte > 1.5:
                score -= 1
                reasons.append(f"elevated leverage (D/E {dte:.2f}x)")

        if vs_20d is not None:
            if vs_20d > 0:
                score += 1
                reasons.append(f"trading {vs_20d:+.2f}% above 20-period avg")
            else:
                score -= 1
                reasons.append(f"trading {vs_20d:+.2f}% below 20-period avg")

        if deliv_pct is not None and deliv_pct >= 50:
            score += 1
            reasons.append(f"strong delivery share ({deliv_pct:.1f}%)")

        missing_count = len(data_quality.get("missing_fundamental_fields", []))
        caveat = " (Data-Caveated)" if missing_count > 3 else ""

        if score >= 2:
            stance = f"Constructive / Fundamental Quality{caveat}"
            action_guidance = (
                f"Profitability, balance-sheet stability, and historical signals lean constructive for {symbol}. "
                f"Cross-check with the ML Trend Predictor tab for short-term timing."
            )
        elif score <= -1:
            stance = f"Cautious / Watchlist{caveat}"
            action_guidance = (
                f"Margin, leverage, or price momentum signals warrant caution on {symbol}; "
                f"monitor upcoming earnings before committing capital."
            )
        else:
            stance = f"Neutral / Hold for Verification{caveat}"
            action_guidance = (
                f"Balanced fundamental and historical indicators for {symbol}; "
                f"combine with the ML Trend Predictor and live price chart for confirmation."
            )

        one_liner = (
            f"{symbol}: {stance.split(' (')[0]} — "
            + (", ".join(reasons) if reasons else "evaluated available fundamental and historical metrics")
            + "."
        )

        return {
            "one_liner": one_liner,
            "stance": stance,
            "action_guidance": action_guidance,
            "disclaimer": "Analytical summary combining static dataset and financial statement metrics; not investment advice.",
        }

    def run(self, raw_ticker: str, market: str | None = None) -> dict:
        symbol = self.normalize_symbol(raw_ticker)
        df, source_ref, is_static = self._load_symbol_df(symbol, market)
        live = self._fetch_live_fundamentals(symbol, market)

        latest_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else None
        latest_date = (
            latest_row["Date"].strftime("%Y-%m-%d")
            if "Date" in df.columns and pd.notna(latest_row.get("Date"))
            else None
        )

        revenue_earnings = self.analyze_revenue_and_earnings(latest_row, prev_row, live)
        profitability = self.analyze_profitability(latest_row, live)
        debt_stability = self.analyze_debt_and_stability(latest_row, live)
        valuation = self.analyze_valuation_and_ratios(live)
        historical = self.analyze_historical_comparison(df)
        peers = self.analyze_peer_comparison(symbol)
        data_quality = self.identify_missing_or_inconsistent_data(df, live, is_static)
        takeaway = self.build_investment_takeaway(
            symbol, historical, profitability, debt_stability, valuation, data_quality
        )

        source_label = (
            f"Static Dataset ({source_ref}) + Live Statement Backfill"
            if is_static and live.get("has_live_statements")
            else (f"Static Dataset ({source_ref})" if is_static else source_ref)
        )

        return {
            "agent": self.name,
            "ticker": symbol,
            "market": market or "NSE",
            "company_name": live.get("company_name") or symbol,
            "as_of_date": latest_date,
            "investment_takeaway": takeaway,
            "revenue_and_earnings": revenue_earnings,
            "profitability": profitability,
            "debt_and_stability": debt_stability,
            "valuation_and_ratios": valuation,
            "historical_comparison": historical,
            "peer_comparison": peers,
            "data_quality_issues": data_quality,
            "source": source_label,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }