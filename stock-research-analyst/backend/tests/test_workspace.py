from tests.conftest import login, register


def test_preferences_defaults_and_update(client, alice):
    assert client.get("/api/preferences").json() == {"market": "NASDAQ", "analysis_period": "1Y"}
    r = client.put("/api/preferences", json={"market": "NSE", "analysis_period": "6M"}, headers=alice)
    assert r.status_code == 200
    assert client.get("/api/preferences").json() == {"market": "NSE", "analysis_period": "6M"}
    bad = client.put("/api/preferences", json={"market": "LSE", "analysis_period": "6M"}, headers=alice)
    assert bad.status_code == 422


def test_stock_search(client, alice):
    r = client.get("/api/stocks/search", params={"q": "tcs", "market": "NSE"})
    assert r.status_code == 200
    assert r.json()[0]["provider_symbol"] == "TCS.NS"
    assert client.get("/api/stocks/search", params={"q": "apple"}).json()[0]["ticker"] == "AAPL"


def test_watchlist_add_list_duplicate_remove(client, alice):
    r = client.post("/api/watchlist", json={"ticker": "aapl", "market": "NASDAQ"}, headers=alice)
    assert r.status_code == 201
    saved_id = r.json()["saved_stock_id"]
    assert client.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}, headers=alice).status_code == 409
    assert client.post("/api/watchlist", json={"ticker": "ZZZZ", "market": "NASDAQ"}, headers=alice).status_code == 404
    assert [s["ticker"] for s in client.get("/api/watchlist").json()] == ["AAPL"]
    assert client.delete(f"/api/watchlist/{saved_id}", headers=alice).status_code == 204
    assert client.get("/api/watchlist").json() == []


def test_watchlist_is_per_user(client):
    register(client, email="alice@gmail.com")
    alice_h = login(client, email="alice@gmail.com")
    saved_id = client.post("/api/watchlist", json={"ticker": "AAPL", "market": "NASDAQ"}, headers=alice_h).json()["saved_stock_id"]
    client.post("/api/auth/logout")

    register(client, email="bob@gmail.com", name="Bob Test")
    bob_h = login(client, email="bob@gmail.com")
    assert client.get("/api/watchlist").json() == []
    assert client.delete(f"/api/watchlist/{saved_id}", headers=bob_h).status_code == 404  # can't touch Alice's


def test_research_uses_preferences_and_completes(client, alice):
    client.put("/api/preferences", json={"market": "NSE", "analysis_period": "3M"}, headers=alice)
    r = client.post("/api/research", json={"ticker": "tcs"}, headers=alice)
    assert r.status_code == 201
    task = r.json()
    assert (task["ticker"], task["market"], task["analysis_period"]) == ("TCS", "NSE", "3M")

    # background stub runs right after the response in TestClient
    detail = client.get(f"/api/research/{task['task_id']}").json()
    assert detail["status"] == "Completed"
    assert "TCS" in detail["report"]
    assert len(client.get("/api/research").json()) == 1


def test_research_rejects_wrong_market_symbol(client, alice):
    r = client.post("/api/research", json={"ticker": "AAPL", "market": "NSE"}, headers=alice)
    assert r.status_code == 422


def test_research_history_is_isolated_per_user(client):
    register(client, email="alice@gmail.com")
    alice_h = login(client, email="alice@gmail.com")
    task_id = client.post("/api/research", json={"ticker": "AAPL", "market": "NASDAQ"}, headers=alice_h).json()["task_id"]
    client.post("/api/auth/logout")

    register(client, email="bob@gmail.com", name="Bob Test")
    login(client, email="bob@gmail.com")
    assert client.get("/api/research").json() == []
    assert client.get(f"/api/research/{task_id}").status_code == 404
