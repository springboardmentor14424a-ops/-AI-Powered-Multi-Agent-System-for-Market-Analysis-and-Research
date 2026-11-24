"""
Test Suite: Company Search Bar, Autocomplete, and Exchange Validation
Validates:
1. Strict exchange isolation across NSE, BSE, NASDAQ, and NYSE.
2. Accurate search suggestions matching ticker prefixes, company name prefixes, and word prefixes.
3. Strict exclusion of unrelated companies (e.g., 'P' does not return Meta Platforms).
4. No results found: returns empty list for non-matching queries (e.g. 'XYZ123'); zero fabrication.
5. Search validation: prevents submission of invalid company names or symbols.
"""

import pytest

@pytest.fixture
def auth_headers(client):
    """Registers and authenticates test user for protected endpoint testing."""
    reg = client.post("/api/auth/register", json={
        "full_name": "Search Validator",
        "email": "search.validator@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    login = client.post("/api/auth/login", json={
        "email": "search.validator@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_exchange_specific_search_suggestions(client):
    """Verifies prefix matching on symbol and name for NSE companies."""
    # 1. REL -> Reliance Industries Limited
    r_rel = client.get("/api/watchlist/companies", params={"market": "NSE", "q": "REL"})
    assert r_rel.status_code == 200
    rel_data = r_rel.json()
    assert len(rel_data) >= 1
    assert any(c["ticker"] == "RELIANCE" for c in rel_data)
    assert all(c["market"] == "NSE" for c in rel_data)

    # 2. TCS -> Tata Consultancy Services Ltd (symbol match)
    r_tcs = client.get("/api/watchlist/companies", params={"market": "NSE", "q": "TCS"})
    assert r_tcs.status_code == 200
    tcs_data = r_tcs.json()
    assert len(tcs_data) >= 1
    assert any(c["ticker"] == "TCS" for c in tcs_data)
    assert all(c["market"] == "NSE" for c in tcs_data)

    # 3. INF -> Infosys Limited
    r_inf = client.get("/api/watchlist/companies", params={"market": "NSE", "q": "INF"})
    assert r_inf.status_code == 200
    inf_data = r_inf.json()
    assert len(inf_data) >= 1
    assert any(c["ticker"] == "INFY" for c in inf_data)
    assert all(c["market"] == "NSE" for c in inf_data)


def test_no_results_found_without_fabrication(client):
    """Verifies that non-matching search queries return an empty list and no fake companies."""
    r_xyz = client.get("/api/watchlist/companies", params={"market": "NSE", "q": "XYZ123"})
    assert r_xyz.status_code == 200
    xyz_data = r_xyz.json()
    assert len(xyz_data) == 0, f"Expected 0 results for XYZ123 on NSE, got: {xyz_data}"

    r_market_data = client.get("/api/market-data/search", params={"market": "NSE", "q": "XYZ123"})
    assert r_market_data.status_code == 200
    assert len(r_market_data.json()) == 0


def test_p_query_exclusion_of_unrelated_companies(client):
    """
    Verifies that searching 'P' on NSE returns ONLY genuine NSE matches
    and NEVER returns Meta Platforms or unrelated non-P companies.
    """
    r_p = client.get("/api/watchlist/companies", params={"market": "NSE", "q": "P"})
    assert r_p.status_code == 200
    p_data = r_p.json()
    p_tickers = [c["ticker"] for c in p_data]
    p_names = [c["name"] for c in p_data]

    # Meta Platforms is NASDAQ, must NEVER be in NSE
    assert "META" not in p_tickers
    assert "Meta Platforms, Inc." not in p_names

    # All returned companies must strictly belong to NSE
    for c in p_data:
        assert c["market"] == "NSE"
        assert c["name"].lower().startswith("p") or c["ticker"].lower().startswith("p")

    # On NASDAQ, 'P' returns PayPal / Palo Alto, NOT Meta Platforms
    r_nasdaq_p = client.get("/api/watchlist/companies", params={"market": "NASDAQ", "q": "P"})
    assert r_nasdaq_p.status_code == 200
    nasdaq_p_names = [c["name"] for c in r_nasdaq_p.json()]
    assert "Meta Platforms, Inc." not in nasdaq_p_names
    assert any("PayPal" in n for n in nasdaq_p_names)


def test_research_task_submission_validation(client, auth_headers):
    """
    Validates that invalid tickers are rejected with HTTP 400
    and valid tickers are accepted.
    """
    # 1. Invalid ticker XYZ123 on NSE
    invalid_res = client.post("/api/tasks", json={
        "ticker": "XYZ123",
        "market": "NSE",
        "requested_period": "1 Month"
    }, headers=auth_headers)
    assert invalid_res.status_code == 400
    assert "not listed on the NSE exchange" in invalid_res.json()["detail"]

    # 2. Mismatched exchange: AAPL on NSE
    mismatch_res = client.post("/api/tasks", json={
        "ticker": "AAPL",
        "market": "NSE",
        "requested_period": "1 Month"
    }, headers=auth_headers)
    assert mismatch_res.status_code == 400
    assert "not listed on the NSE exchange" in mismatch_res.json()["detail"]

    # 3. Valid ticker: TCS on NSE
    valid_res = client.post("/api/tasks", json={
        "ticker": "TCS",
        "market": "NSE",
        "requested_period": "1 Month"
    }, headers=auth_headers)
    assert valid_res.status_code == 201
    assert valid_res.json()["ticker"] == "TCS"
    assert valid_res.json()["market"] == "NSE"


def test_fundamental_analysis_validation(client, auth_headers):
    """Validates that fundamental analysis rejects invalid tickers."""
    invalid_res = client.post("/api/fundamental/analyze", json={
        "ticker": "XYZ123",
        "market": "NSE"
    }, headers=auth_headers)
    assert invalid_res.status_code == 400
    assert "not listed on the NSE exchange" in invalid_res.json()["detail"]
