
from yahoo_data_service import get_stock_data, get_stock_list

print("Checking available companies...")

companies = get_stock_list()

print("Total companies:", len(companies))
print("\nFirst 5 companies:")

for company in companies[:5]:
    print(company)

print("\nTesting Apple stock analysis...")

result = get_stock_data(
    ticker="AAPL",
    analysis_period="3 Months"
)

for key, value in result.items():
    print(f"{key}: {value}")
