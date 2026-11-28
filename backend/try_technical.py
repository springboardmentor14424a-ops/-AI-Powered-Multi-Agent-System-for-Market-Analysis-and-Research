from technical_analysis import run_technical_agent

result = run_technical_agent("RELIANCE.NS")
rows = result["chart_data"]
print("Number of chart rows:", len(rows))
print("First row:", rows[0])
print("Last row:", rows[-1])
