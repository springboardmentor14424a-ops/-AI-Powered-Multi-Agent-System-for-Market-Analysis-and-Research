
import yfinance as yf

symbols = [
    "INFY.NS",
    "TCS.NS",
    "HCLTECH.NS",
    "WIPRO.NS",
    "TECHM.NS"
]

for symbol in symbols:

    print("\nChecking:", symbol)

    try:
        stock = yf.Ticker(symbol)
        info = stock.get_info()

        print("Company:", info.get("longName"))
        print("Industry:", info.get("industry"))
        print("P/E:", info.get("trailingPE"))
        print("P/B:", info.get("priceToBook"))

    except Exception as error:
        print("Error:", error)
