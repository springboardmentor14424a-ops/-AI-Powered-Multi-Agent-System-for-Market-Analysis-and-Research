
from app.services.stock_data_service import get_stock_analysis

try:
    result = get_stock_analysis("INFY.NS")

    print("\n========== STOCK SUMMARY ==========")

    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    print("\n========== LAST 10 DAYS ==========")

    data = result["historical_data"]

    columns = [
        "Close",
        "Daily_Change",
        "Daily_Return_Percent",
        "MA5",
        "MA20",
        "MA50",
        "MA200",
        "RSI",
        "MACD",
        "MACD_Signal",
    ]

    print(data[columns].tail(10))

except Exception as error:
    print("Stock analysis failed:", error)
