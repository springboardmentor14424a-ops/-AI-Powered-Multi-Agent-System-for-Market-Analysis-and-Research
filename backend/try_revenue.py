from fundamental_analysis import revenue_growth

# Reliance "Total Revenue" copied from your Yahoo response
statements = {
    "income_statement": {
        "Total Revenue": {
            "2026-03-31": 10572190000000,
            "2025-03-31": 9646930000000,
            "2024-03-31": 9010640000000,
            "2023-03-31": 8778350000000,
            "2022-03-31": None,
        }
    }
}

print(revenue_growth(statements))
