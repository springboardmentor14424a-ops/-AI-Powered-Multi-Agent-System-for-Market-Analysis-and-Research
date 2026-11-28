import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
info = ticker.info

print("Share price:", info.get("currentPrice"))
print("Profit per share (EPS):", info.get("trailingEps"))
print("Book value per share:", info.get("bookValue"))
print("Yahoo's own P/E:", info.get("trailingPE"))
print("Yahoo's own P/B:", info.get("priceToBook"))
