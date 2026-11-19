
def resolve_ticker(symbol: str, market: str):
    symbol = symbol.strip().upper()
    market = market.strip().upper()

    if not symbol:
        raise ValueError("Stock symbol is required")

    if market == "NSE":
        if symbol.endswith((".NS", ".BO")):
            raise ValueError("Enter the symbol without an exchange suffix")
        return symbol + ".NS"

    elif market == "BSE":
        if symbol.endswith((".NS", ".BO")):
            raise ValueError("Enter the symbol without an exchange suffix")
        return symbol + ".BO"

    elif market in ["NASDAQ", "NYSE"]:
        if symbol.endswith((".NS", ".BO")):
            raise ValueError("Invalid ticker for selected market")
        return symbol

    else:
        raise ValueError("Unsupported stock market")
