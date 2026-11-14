import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("==================================================")
    print("RUNNING COMPANY AUTOCOMPLETE SPECIFICATION TESTS")
    print("==================================================")

    # 1. Test NSE + 'TAT' (Prefix matching on company name)
    r1 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NSE", "q": "TAT"})
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    nse_tat = r1.json()
    assert len(nse_tat) > 0, "Expected at least 1 match for NSE + TAT"
    print(f"Test 1 Passed: NSE + 'TAT' returned {len(nse_tat)} companies.")
    names = [c["name"] for c in nse_tat]
    assert any("Tata Motors" in n for n in names), "Tata Motors must be present in NSE"
    assert any("Tata Steel" in n for n in names), "Tata Steel must be present in NSE"
    for c in nse_tat:
        assert c["market"] == "NSE", f"Leaked non-NSE market: {c['market']}"
    print("   -> All results strictly belong to NSE (Tata Motors, Tata Steel, etc. verified)")

    # 2. Test BSE + 'TAT'
    r2 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "BSE", "q": "TAT"})
    assert r2.status_code == 200
    bse_tat = r2.json()
    assert len(bse_tat) > 0
    for c in bse_tat:
        assert c["market"] == "BSE", f"Leaked non-BSE market: {c['market']}"
    print(f"Test 2 Passed: BSE + 'TAT' returned {len(bse_tat)} companies, all strictly BSE.")

    # 3. Test NASDAQ + 'TAT' (Should return NO results found / empty list)
    r3 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NASDAQ", "q": "TAT"})
    assert r3.status_code == 200
    nasdaq_tat = r3.json()
    assert len(nasdaq_tat) == 0, f"Expected 0 results for NASDAQ + TAT, got {len(nasdaq_tat)}"
    print("Test 3 Passed: NASDAQ + 'TAT' returned 0 results (triggers 'No results found', no leak from NSE/BSE).")

    # 4. Test Case-Insensitivity ('app' vs 'APP' vs 'Apple')
    r4_lower = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NASDAQ", "q": "app"})
    r4_upper = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NASDAQ", "q": "APP"})
    assert r4_lower.json() == r4_upper.json(), "Case-insensitivity failed"
    nasdaq_app = r4_lower.json()
    assert any(c["ticker"] == "AAPL" for c in nasdaq_app), "Apple Inc. (AAPL) should match 'app'"
    for c in nasdaq_app:
        assert c["market"] == "NASDAQ", f"Leaked non-NASDAQ market: {c['market']}"
    print("Test 4 Passed: Case-insensitive search verified ('app' matches Apple Inc. on NASDAQ).")

    # 5. Test NYSE Isolation (Apple Inc. must NOT be returned for NYSE)
    r5 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NYSE", "q": "Apple"})
    nyse_apple = r5.json()
    assert len(nyse_apple) == 0, "Apple Inc. must not be returned for NYSE"
    print("Test 5 Passed: Exchange isolation verified (Apple not present in NYSE).")

    # 6. Test User Issue: Typing 'P' on NASDAQ must NOT return 'Meta Platforms'
    r6 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NASDAQ", "q": "P"})
    assert r6.status_code == 200
    nasdaq_p = r6.json()
    p_names = [c["name"] for c in nasdaq_p]
    assert "Meta Platforms, Inc." not in p_names, "CRITICAL ERROR: 'Meta Platforms, Inc.' must NOT be returned for prefix 'P'!"
    for c in nasdaq_p:
        assert c["name"].lower().startswith("p"), f"Non-prefix company found: {c['name']}"
        assert c["market"] == "NASDAQ"
    print(f"Test 6 Passed: NASDAQ + 'P' returned {len(nasdaq_p)} companies, strictly starting with P (Meta Platforms excluded).")

    # 7. Test Typing 'M' on NASDAQ must return 'Meta Platforms'
    r7 = requests.get(f"{BASE_URL}/watchlist/companies", params={"market": "NASDAQ", "q": "M"})
    assert r7.status_code == 200
    nasdaq_m = r7.json()
    m_names = [c["name"] for c in nasdaq_m]
    assert "Meta Platforms, Inc." in m_names, "'Meta Platforms, Inc.' must be returned for prefix 'M'!"
    for c in nasdaq_m:
        assert c["name"].lower().startswith("m"), f"Non-prefix company found: {c['name']}"
    print("Test 7 Passed: NASDAQ + 'M' correctly returns Meta Platforms, Inc. and only M-prefix companies.")

    # 8. Test strict parameter on /search endpoint
    r8 = requests.get(f"{BASE_URL}/watchlist/search", params={"q": "TAT", "market": "NSE", "strict": True})
    assert r8.status_code == 200
    assert len(r8.json()) > 0
    for c in r8.json():
        assert c["market"] == "NSE"
    print("Test 8 Passed: /watchlist/search with strict=True returns only NSE companies.")

    print("==================================================")
    print("ALL COMPANY AUTOCOMPLETE SPECIFICATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
