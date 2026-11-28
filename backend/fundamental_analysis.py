from datetime import datetime, timezone

import yfinance as yf


def _clean(series):
    """Keep only real numbers. Years where Yahoo gave null are dropped."""
    return {d: v for d, v in (series or {}).items() if v is not None}


def revenue_growth(statements):
    """Revenue for each year, and how much it grew compared with the year before."""
    revenue = _clean(statements["income_statement"].get("Total Revenue"))
    dates = sorted(revenue)  # oldest year first
    growth = {}
    for i in range(1, len(dates)):
        previous = revenue[dates[i - 1]]
        current = revenue[dates[i]]
        if previous:  # avoids dividing by zero
            growth[dates[i]] = round((current - previous) / previous * 100, 2)
    return {"revenue": revenue, "growth_percent": growth}


def profitability(statements):
    """Profit margins (how much profit per Rs 100 of revenue) and net profit growth."""
    income = statements["income_statement"]
    revenue = _clean(income.get("Total Revenue"))

    result = {}
    for label, row in [
        ("gross_margin_percent", "Gross Profit"),
        ("operating_margin_percent", "Operating Income"),
        ("net_margin_percent", "Net Income"),
    ]:
        series = _clean(income.get(row))
        result[label] = {
            d: round(series[d] / revenue[d] * 100, 2)
            for d in sorted(series)
            if d in revenue and revenue[d]
        }

    net = _clean(income.get("Net Income"))
    dates = sorted(net)
    growth = {}
    for i in range(1, len(dates)):
        if net[dates[i - 1]]:
            growth[dates[i]] = round(
                (net[dates[i]] - net[dates[i - 1]]) / net[dates[i - 1]] * 100, 2
            )
    result["net_income_growth_percent"] = growth
    return result


def debt_and_stability(statements):
    """Debt level, return on equity (ROE), and how much of the company is funded by borrowing."""
    bs = statements["balance_sheet"]
    income = statements["income_statement"]

    debt = _clean(bs.get("Total Debt"))
    equity = _clean(bs.get("Stockholders Equity"))
    cash = _clean(bs.get("Cash And Cash Equivalents"))
    assets = _clean(bs.get("Total Assets"))
    liabilities = _clean(bs.get("Total Liabilities Net Minority Interest"))
    net_income = _clean(income.get("Net Income"))
    current_assets = _clean(bs.get("Current Assets"))
    current_liabilities = _clean(bs.get("Current Liabilities"))

    def ratio(top, bottom, times=1):
        return {
            d: round(top[d] / bottom[d] * times, 2)
            for d in sorted(top)
            if d in bottom and bottom[d]
        }

    result = {
        "debt_to_equity": ratio(debt, equity),
        "net_debt": {d: debt[d] - cash[d] for d in sorted(debt) if d in cash},
        "roe_percent": ratio(net_income, equity, 100),
        "liabilities_to_assets_percent": ratio(liabilities, assets, 100),
    }

    if current_assets and current_liabilities:
        result["current_ratio"] = ratio(current_assets, current_liabilities)
    else:
        result["current_ratio"] = "not available"
    return result


def valuation_ratios(ticker):
    """P/E and P/B: how many rupees investors pay for Rs 1 of profit and Rs 1 of net worth."""
    if not ticker:
        return {
            "pe_ratio": "not available",
            "pb_ratio": "not available",
            "note": "ticker not provided",
        }
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return {
            "pe_ratio": "not available",
            "pb_ratio": "not available",
            "note": "could not fetch valuation data",
        }

    price = info.get("currentPrice")
    eps = info.get("trailingEps")   # profit per share
    book = info.get("bookValue")    # net worth per share

    # P/E only makes sense when the company earns a profit (EPS above zero)
    if price and eps and eps > 0:
        pe = round(price / eps, 2)
    else:
        pe = "not available"

    # P/B only makes sense when net worth is above zero
    if price and book and book > 0:
        pb = round(price / book, 2)
    else:
        pb = "not available"

    return {
        "share_price": price,
        "eps": eps,
        "book_value_per_share": book,
        "pe_ratio": pe,
        "pb_ratio": pb,
        "yahoo_pe_for_cross_check": info.get("trailingPE"),
        "yahoo_pb_for_cross_check": info.get("priceToBook"),
    }


def _trend(series, higher_is_better=True, as_percent_change=True, tolerance=2.0):
    """Compares the oldest year with the latest year and says improving, declining or stable.
    Changes smaller than 'tolerance' are called stable."""
    dates = sorted(series)
    if len(dates) < 2:
        return "not available"

    first_year, latest_year = dates[0], dates[-1]
    first, latest = series[first_year], series[latest_year]

    if as_percent_change:
        if not first:
            return "not available"
        change = round((latest - first) / abs(first) * 100, 2)
        unit = "percent change"
    else:
        change = round(latest - first, 2)
        unit = "difference (points)"

    if abs(change) <= tolerance:
        direction = "stable"
    elif (change > 0) == higher_is_better:
        direction = "improving"
    else:
        direction = "declining"

    return {
        "first_year": first_year,
        "first_value": first,
        "latest_year": latest_year,
        "latest_value": latest,
        "change": change,
        "change_unit": unit,
        "direction": direction,
    }


def _pretty(value, is_money):
    """Makes numbers easy to read: money in billions, ratios with 2 decimals."""
    if is_money:
        return f"{value / 1e9:,.2f} billion"
    return f"{value:,.2f}"


def historical_comparison(statements):
    """Compares the oldest year with the latest year for the key numbers."""
    income = statements["income_statement"]
    revenue = _clean(income.get("Total Revenue"))
    net_income = _clean(income.get("Net Income"))
    profit = profitability(statements)
    debt = debt_and_stability(statements)

    results = {
        "revenue": _trend(revenue, True, True, 2.0),
        "net_income": _trend(net_income, True, True, 2.0),
        "operating_margin_percent": _trend(
            profit["operating_margin_percent"], True, False, 0.5
        ),
        "net_margin_percent": _trend(profit["net_margin_percent"], True, False, 0.5),
        "roe_percent": _trend(debt["roe_percent"], True, False, 0.5),
        # for debt, lower is better
        "debt_to_equity": _trend(debt["debt_to_equity"], False, False, 0.05),
    }

    # Plain-language lines built only from the numbers above (no guessing)
    labels = {
        "revenue": "Revenue",
        "net_income": "Net profit",
        "operating_margin_percent": "Operating margin (%)",
        "net_margin_percent": "Net margin (%)",
        "roe_percent": "Return on equity (%)",
        "debt_to_equity": "Debt-to-equity",
    }
    money_keys = {"revenue", "net_income"}  # these are big money amounts

    summary = []
    for key, label in labels.items():
        r = results[key]
        if isinstance(r, dict):
            m = key in money_keys
            summary.append(
                f"{label}: {_pretty(r['first_value'], m)} in {r['first_year']} to "
                f"{_pretty(r['latest_value'], m)} in {r['latest_year']} "
                f"({r['change']} {r['change_unit']}) - {r['direction']}"
            )
        else:
            summary.append(f"{label}: not enough data to compare")

    return {"comparison": results, "summary": summary}


def data_quality_check(statements, debt_result, valuation):
    """Looks for missing or inconsistent numbers and lists each problem in plain words."""
    issues = []
    income = statements["income_statement"]
    bs = statements["balance_sheet"]

    # 1. Key numbers that are missing completely, or missing for some years
    required = [
        (income, "Total Revenue", "Revenue"),
        (income, "Gross Profit", "Gross profit"),
        (income, "Operating Income", "Operating income"),
        (income, "Net Income", "Net income"),
        (bs, "Total Debt", "Total debt"),
        (bs, "Stockholders Equity", "Shareholders' equity"),
        (bs, "Cash And Cash Equivalents", "Cash"),
        (bs, "Total Assets", "Total assets"),
        (bs, "Total Liabilities Net Minority Interest", "Total liabilities"),
    ]
    for section, row, label in required:
        raw = section.get(row)
        if not raw or not _clean(raw):
            issues.append(f"{label} is not available from the data source.")
            continue
        missing_years = sorted(d for d, v in raw.items() if v is None)
        if missing_years:
            issues.append(f"{label} is missing for: {', '.join(missing_years)}.")

    # 2. Too few years of history
    revenue = _clean(income.get("Total Revenue"))
    if 0 < len(revenue) < 3:
        issues.append(
            f"Only {len(revenue)} year(s) of data found, so trends may not be reliable."
        )

    # 3. Numbers that do not make sense
    gross = _clean(income.get("Gross Profit"))
    net = _clean(income.get("Net Income"))
    equity = _clean(bs.get("Stockholders Equity"))
    for d in sorted(revenue):
        if revenue[d] <= 0:
            issues.append(f"Revenue is zero or negative in {d}, which looks wrong.")
        if d in gross and gross[d] > revenue[d] > 0:
            issues.append(f"Gross profit is higher than revenue in {d}, which looks wrong.")
        if d in net and net[d] > revenue[d] > 0:
            issues.append(f"Net income is higher than revenue in {d}, which looks wrong.")
    for d in sorted(equity):
        if equity[d] <= 0:
            issues.append(
                f"Shareholders' equity is zero or negative in {d}, "
                "so ROE and debt-to-equity are not meaningful."
            )

    # Balance sheet should balance: assets = liabilities + equity (including minority interest)
    assets = _clean(bs.get("Total Assets"))
    liabilities = _clean(bs.get("Total Liabilities Net Minority Interest"))
    total_equity = _clean(bs.get("Total Equity Gross Minority Interest"))
    for d in sorted(assets):
        if d in liabilities and d in total_equity and assets[d]:
            gap = abs(assets[d] - (liabilities[d] + total_equity[d])) / abs(assets[d])
            if gap > 0.01:
                issues.append(
                    f"Balance sheet in {d} does not balance "
                    f"(difference is {round(gap * 100, 2)}% of total assets)."
                )

    # 4. Ratios that could not be calculated
    if debt_result.get("current_ratio") == "not available":
        issues.append(
            "Current ratio could not be calculated because current assets and "
            "current liabilities are not provided by the data source."
        )
    if valuation.get("pe_ratio") == "not available":
        issues.append(
            "P/E ratio is not available (profit per share is missing or not positive)."
        )
    if valuation.get("pb_ratio") == "not available":
        issues.append(
            "P/B ratio is not available (book value per share is missing or not positive)."
        )
    return issues


# Companies to compare against. Add more companies here later if needed.
PEER_GROUPS = {
    "RELIANCE.NS": ["ONGC.NS", "IOC.NS", "BPCL.NS"],
}


def _statements_for(ticker):
    """Downloads a company's income statement and balance sheet from Yahoo
    and arranges them in the same format the other functions already use."""
    t = yf.Ticker(ticker)

    def to_rows(df):
        out = {}
        if df is None or df.empty:
            return out
        for item, row in df.iterrows():
            out[str(item)] = {
                c.strftime("%Y-%m-%d"): (None if v != v else float(v))
                for c, v in row.items()
            }
        return out

    return {
        "income_statement": to_rows(t.financials),
        "balance_sheet": to_rows(t.balance_sheet),
    }


def _latest(series):
    """Returns the value of the most recent year, or 'not available'."""
    series = _clean(series)
    if not series:
        return "not available"
    return series[max(series)]


def _snapshot(ticker):
    """The key numbers (latest year) for one company."""
    statements = _statements_for(ticker)
    growth = revenue_growth(statements)
    profit = profitability(statements)
    debt = debt_and_stability(statements)
    value = valuation_ratios(ticker)
    return {
        "revenue_growth_percent": _latest(growth["growth_percent"]),
        "operating_margin_percent": _latest(profit["operating_margin_percent"]),
        "net_margin_percent": _latest(profit["net_margin_percent"]),
        "roe_percent": _latest(debt["roe_percent"]),
        "debt_to_equity": _latest(debt["debt_to_equity"]),
        "pe_ratio": value.get("pe_ratio", "not available"),
        "pb_ratio": value.get("pb_ratio", "not available"),
    }


def peer_comparison(ticker, peers=None):
    """Puts the company's key numbers next to similar companies (peers)."""
    peers = peers or PEER_GROUPS.get(ticker)
    if not ticker or not peers:
        return {"note": "No peer companies are set for this stock, so no comparison was done."}

    companies = {}
    notes = []
    for name in [ticker] + list(peers):
        try:
            companies[name] = _snapshot(name)
        except Exception:
            notes.append(f"Could not fetch data for {name}.")

    if ticker not in companies:
        return {"note": f"Could not fetch data for {ticker}, so no comparison was done.",
                "data_issues": notes}

    labels = {
        "revenue_growth_percent": "Revenue growth (%)",
        "operating_margin_percent": "Operating margin (%)",
        "net_margin_percent": "Net margin (%)",
        "roe_percent": "Return on equity (%)",
        "debt_to_equity": "Debt-to-equity",
        "pe_ratio": "P/E ratio",
        "pb_ratio": "P/B ratio",
    }

    summary = []
    for key, label in labels.items():
        own = companies[ticker][key]
        others = [
            companies[p][key]
            for p in peers
            if p in companies and isinstance(companies[p][key], (int, float))
        ]
        if not isinstance(own, (int, float)) or not others:
            summary.append(f"{label}: not enough data to compare.")
            continue
        average = round(sum(others) / len(others), 2)
        if own > average:
            position = "above"
        elif own < average:
            position = "below"
        else:
            position = "equal to"
        summary.append(
            f"{label}: {ticker} is {own}, which is {position} the peer average of {average}."
        )

    return {
        "company": ticker,
        "peers": [p for p in peers if p in companies],
        "metrics": companies,
        "versus_peer_average": summary,
        "data_issues": notes,
        "note": "Latest financial year for each company. Peers are similar-sector companies, not exact matches.",
    }


def run_fundamental_agent(financials, ticker=None):
    """Runs all the analyses on one company's Yahoo data and packs the result in one fixed format."""
    statements = financials["statements"]
    ticker = ticker or financials.get("ticker") or financials.get("symbol")

    debt_result = debt_and_stability(statements)
    valuation = valuation_ratios(ticker)

    issues = list(financials.get("missing_items", []) or [])
    issues += data_quality_check(statements, debt_result, valuation)

    return {
        "agent_name": "fundamental_analysis",
        "revenue_analysis": revenue_growth(statements),
        "profitability_analysis": profitability(statements),
        "debt_stability_analysis": debt_result,
        "valuation_analysis": valuation,
        "historical_comparison": historical_comparison(statements),
        "peer_comparison": peer_comparison(ticker),
        "data_issues": issues,
        "data_quality_status": "no issues found" if not issues else "issues found",
        "source": financials.get("source"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result_type": "calculated_metrics",
    }
