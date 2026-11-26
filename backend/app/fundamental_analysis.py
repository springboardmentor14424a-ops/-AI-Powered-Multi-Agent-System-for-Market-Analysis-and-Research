from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from .market_data import (
    ALLOWED_MARKETS,
    _belongs_to_market,
    _call_provider,
    _number,
    _source,
    build_market_data,
    normalize_ticker,
    YFinanceError,
)
from .schemas import (
    FinancialPeriod,
    FundamentalAnalysisResponse,
    FundamentalMetrics,
    PeerComparison,
)
from .market_data import ALLOWED_PERIODS


def _statement_value(statement: Any, row_names: tuple[str, ...], period: Any) -> float | None:
    if statement is None or statement.empty:
        return None
    for row_name in row_names:
        if row_name in statement.index and period in statement.columns:
            return _number(statement.loc[row_name, period])
    return None


def _period_label(period: Any) -> str:
    period_date = getattr(period, "date", None)
    if period_date:
        return period_date().isoformat()
    return str(period)


def _statement_periods(*statements: Any) -> list[Any]:
    periods: set[Any] = set()
    for statement in statements:
        if statement is not None and not statement.empty:
            periods.update(statement.columns)
    return sorted(periods, key=_period_label, reverse=True)


def _growth(latest: float | None, previous: float | None) -> float | None:
    if latest is None or previous is None or previous <= 0:
        return None
    return (latest - previous) / previous * 100


def _percent(value: float | None) -> float | None:
    return value * 100 if value is not None else None


def _financial_periods(
    income_statement: Any,
    balance_sheet: Any,
    cash_flow: Any,
) -> list[FinancialPeriod]:
    periods = _statement_periods(income_statement, balance_sheet, cash_flow)[:3]
    return [
        FinancialPeriod(
            period=_period_label(period),
            revenue=_statement_value(income_statement, ("Total Revenue", "Operating Revenue"), period),
            net_income=_statement_value(
                income_statement,
                ("Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"),
                period,
            ),
            total_debt=_statement_value(balance_sheet, ("Total Debt",), period),
            cash=_statement_value(
                balance_sheet,
                ("Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"),
                period,
            ),
            shareholders_equity=_statement_value(
                balance_sheet,
                ("Stockholders Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"),
                period,
            ),
        )
        for period in periods
    ]


def _peer_comparisons(
    ticker: str,
    market: str,
    info: dict[str, Any],
) -> tuple[list[PeerComparison], str | None]:
    industry = info.get("industry")
    if not industry:
        return [], "Peer comparison unavailable because Yahoo Finance did not provide an industry."

    try:
        search = _call_provider(
            f"search for {industry} peers",
            lambda: yf.Search(industry, max_results=16, news_count=0, lists_count=0),
        )
    except YFinanceError:
        return [], "Peer comparison could not be retrieved from Yahoo Finance."

    peers: list[PeerComparison] = []
    seen_tickers = {ticker}
    for quote in search.quotes:
        peer_ticker = quote.get("symbol")
        if (
            not peer_ticker
            or peer_ticker in seen_tickers
            or not _belongs_to_market(peer_ticker, quote.get("exchange"), market)
        ):
            continue
        seen_tickers.add(peer_ticker)
        try:
            peer_info = _call_provider(
                f"retrieve company information for peer {peer_ticker}",
                lambda: yf.Ticker(peer_ticker).get_info(),
            )
        except YFinanceError:
            continue
        if not isinstance(peer_info, dict):
            continue
        if str(peer_info.get("industry", "")).casefold() != str(industry).casefold():
            continue

        peer = PeerComparison(
            ticker=peer_ticker,
            company_name=peer_info.get("shortName") or peer_info.get("longName") or peer_ticker,
            trailing_pe=_number(peer_info.get("trailingPE")),
            price_to_book=_number(peer_info.get("priceToBook")),
            return_on_equity_percent=_percent(_number(peer_info.get("returnOnEquity"))),
            profit_margin_percent=_percent(_number(peer_info.get("profitMargins"))),
            debt_to_equity_percent=_number(peer_info.get("debtToEquity")),
        )
        if any(
            value is not None
            for value in (
                peer.trailing_pe,
                peer.price_to_book,
                peer.return_on_equity_percent,
                peer.profit_margin_percent,
                peer.debt_to_equity_percent,
            )
        ):
            peers.append(peer)
        if len(peers) == 3:
            break

    if not peers:
        return [], f"No comparable companies with available financial metrics were found in {industry}."
    return peers, None


def run_fundamental_analysis(
    ticker: str,
    period: str = "1y",
    market: str = "US",
) -> FundamentalAnalysisResponse:
    if market not in ALLOWED_MARKETS:
        raise ValueError("Market must be US, NSE, or BSE")
    normalized_ticker = normalize_ticker(ticker, market)
    if period not in ALLOWED_PERIODS:
        raise ValueError(f"Period must be one of: {', '.join(sorted(ALLOWED_PERIODS))}")

    stock = _call_provider(
        f"open the Yahoo Finance profile for {normalized_ticker}",
        lambda: yf.Ticker(normalized_ticker),
    )
    info = _call_provider(
        f"retrieve company information for {normalized_ticker}",
        stock.get_info,
    )
    if not isinstance(info, dict):
        info = {}
    income_statement = _call_provider(
        f"retrieve the income statement for {normalized_ticker}",
        lambda: stock.financials,
    )
    balance_sheet = _call_provider(
        f"retrieve the balance sheet for {normalized_ticker}",
        lambda: stock.balance_sheet,
    )
    cash_flow = _call_provider(
        f"retrieve the cash flow statement for {normalized_ticker}",
        lambda: stock.cashflow,
    )
    history = _call_provider(
        f"retrieve historical prices for {normalized_ticker}",
        lambda: stock.history(period=period, auto_adjust=False),
    )
    market_data = build_market_data(normalized_ticker, info, period, history, market)
    financials = _financial_periods(income_statement, balance_sheet, cash_flow)
    peer_comparisons, peer_gap = _peer_comparisons(normalized_ticker, market, info)

    latest = financials[0] if financials else None
    previous = financials[1] if len(financials) > 1 else None
    revenue_growth = _growth(
        latest.revenue if latest else None,
        previous.revenue if previous else None,
    )
    earnings_growth = _growth(
        latest.net_income if latest else None,
        previous.net_income if previous else None,
    )
    equity = latest.shareholders_equity if latest else None
    net_income = latest.net_income if latest else None
    debt = latest.total_debt if latest else None
    roe = _number(info.get("returnOnEquity"))
    if roe is None and net_income is not None and equity is not None and equity > 0:
        roe = net_income / equity
    debt_to_equity = _number(info.get("debtToEquity"))
    if debt_to_equity is None and debt is not None and equity is not None and equity > 0:
        debt_to_equity = debt / equity * 100
    cash = latest.cash if latest else None

    market_cap = _number(info.get("marketCap"))
    current_price = _number(info.get("currentPrice")) or _number(info.get("regularMarketPrice"))
    trailing_pe = _number(info.get("trailingPE"))
    if trailing_pe is None:
        trailing_eps = _number(info.get("trailingEps"))
        if current_price is not None and trailing_eps is not None and trailing_eps > 0:
            trailing_pe = current_price / trailing_eps
    price_to_book = _number(info.get("priceToBook"))
    if price_to_book is None and market_cap is not None and equity is not None and equity > 0:
        price_to_book = market_cap / equity
    profit_margin = _number(info.get("profitMargins"))
    if profit_margin is None and latest and latest.revenue:
        profit_margin = net_income / latest.revenue if net_income is not None else None

    metrics = FundamentalMetrics(
        market_cap=market_cap,
        current_price=current_price,
        trailing_pe=trailing_pe,
        price_to_book=price_to_book,
        return_on_equity_percent=_percent(roe),
        profit_margin_percent=_percent(profit_margin),
        operating_margin_percent=_percent(_number(info.get("operatingMargins"))),
        debt_to_equity_percent=debt_to_equity,
        net_debt=debt - cash if debt is not None and cash is not None else None,
        current_ratio=_number(info.get("currentRatio")),
        revenue_growth_percent=revenue_growth,
        net_income_growth_percent=earnings_growth,
    )

    findings: list[str] = []
    data_gaps: list[str] = []
    if revenue_growth is not None:
        direction = "increased" if revenue_growth >= 0 else "decreased"
        findings.append(f"Revenue {direction} {abs(revenue_growth):.1f}% between the two latest reported periods.")
    if earnings_growth is not None:
        direction = "increased" if earnings_growth >= 0 else "decreased"
        findings.append(f"Net income {direction} {abs(earnings_growth):.1f}% between the two latest reported periods.")
    elif latest and latest.net_income is not None and previous and previous.net_income is not None:
        data_gaps.append("Net income growth was not calculated because the prior period was zero or negative.")
    if metrics.return_on_equity_percent is not None:
        findings.append(f"Return on equity was {metrics.return_on_equity_percent:.1f}% for the latest available data.")
    if metrics.profit_margin_percent is not None:
        findings.append(f"Profit margin was {metrics.profit_margin_percent:.1f}% for the latest available data.")
    if metrics.operating_margin_percent is not None:
        findings.append(f"Operating margin was {metrics.operating_margin_percent:.1f}% for the latest available data.")
    if metrics.debt_to_equity_percent is not None:
        findings.append(f"Debt to equity was {metrics.debt_to_equity_percent:.1f}% in Yahoo Finance data.")
    if metrics.net_debt is not None:
        position = "net debt" if metrics.net_debt >= 0 else "net cash"
        findings.append(f"Latest reported balances imply a {position} position of {abs(metrics.net_debt):,.2f}.")
    if peer_comparisons:
        findings.append(
            f"Compared valuation and financial ratios with {len(peer_comparisons)} companies in {info['industry']}."
        )
    if not findings:
        findings.append("Yahoo Finance returned company data, but there was not enough information to calculate a trend.")

    for label, value in (
        ("Revenue", latest.revenue if latest else None),
        ("Net income", latest.net_income if latest else None),
        ("Total debt", latest.total_debt if latest else None),
        ("Cash", latest.cash if latest else None),
        ("Shareholders' equity", latest.shareholders_equity if latest else None),
        ("Trailing P/E", metrics.trailing_pe),
        ("Price-to-book", metrics.price_to_book),
        ("Return on equity", metrics.return_on_equity_percent),
        ("Current ratio", metrics.current_ratio),
    ):
        if value is None:
            data_gaps.append(f"{label} was not available from Yahoo Finance.")
    if not financials:
        data_gaps.append("No annual financial statements were available.")
    if latest:
        for label, value in (
            ("revenue", latest.revenue),
            ("total debt", latest.total_debt),
            ("cash", latest.cash),
        ):
            if value is not None and value < 0:
                data_gaps.append(
                    f"Yahoo Finance reported negative {label}; verify the source financial statement."
                )
    if peer_gap:
        data_gaps.append(peer_gap)

    retrieved_at = datetime.now(timezone.utc)
    source = _source(normalized_ticker, retrieved_at)
    return FundamentalAnalysisResponse(
        ticker=normalized_ticker,
        market=market,
        company_name=market_data.company_name,
        sector=info.get("sector"),
        industry=info.get("industry"),
        currency=market_data.currency,
        exchange=market_data.exchange,
        metrics=metrics,
        historical_financials=financials,
        peer_comparisons=peer_comparisons,
        findings=findings,
        data_gaps=data_gaps,
        market_data=market_data,
        source=source,
    )
