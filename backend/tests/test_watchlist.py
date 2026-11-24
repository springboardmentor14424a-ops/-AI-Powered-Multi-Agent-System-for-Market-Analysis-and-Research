
def register_and_login(client, email="watchlist@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Watchlist User",
            "email": email,
            "password": "StrongPass123!"
        }
    )
    assert response.status_code == 201

    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "StrongPass123!"
        }
    )


def csrf_headers(client):
    csrf = client.cookies.get("csrf_token")
    return {"X-CSRF-Token": csrf}


def test_add_stock_to_watchlist(client, monkeypatch):
    register_and_login(client)

    # Prevent external Yahoo Finance requests in tests.
    monkeypatch.setattr(
        "app.routes.watchlist.get_stock_price",
        lambda ticker, market: (None, None)
    )

    response = client.post(
        "/api/watchlist",
        json={"ticker": "RELIANCE", "market": "NSE"},
        headers=csrf_headers(client)
    )

    assert response.status_code == 201
    assert response.json()["ticker"] == "RELIANCE"
    assert response.json()["market"] == "NSE"


def test_duplicate_watchlist_stock(client, monkeypatch):
    register_and_login(client)

    monkeypatch.setattr(
        "app.routes.watchlist.get_stock_price",
        lambda ticker, market: (None, None)
    )

    payload = {"ticker": "TCS", "market": "BSE"}
    headers = csrf_headers(client)

    first = client.post(
        "/api/watchlist",
        json=payload,
        headers=headers
    )

    second = client.post(
        "/api/watchlist",
        json=payload,
        headers=headers
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_same_ticker_allowed_on_different_markets(client):
    register_and_login(client)

    headers = csrf_headers(client)

    nse_response = client.post(
        "/api/watchlist",
        json={"ticker": "TCS", "market": "NSE"},
        headers=headers
    )

    bse_response = client.post(
        "/api/watchlist",
        json={"ticker": "TCS", "market": "BSE"},
        headers=headers
    )

    assert nse_response.status_code == 201
    assert bse_response.status_code == 201


def test_get_watchlist_includes_market(client, monkeypatch):
    register_and_login(client)

    monkeypatch.setattr(
        "app.routes.watchlist.get_stock_price",
        lambda ticker, market: (None, None)
    )

    client.post(
        "/api/watchlist",
        json={"ticker": "INFY", "market": "NSE"},
        headers=csrf_headers(client)
    )

    response = client.get("/api/watchlist")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ticker"] == "INFY"
    assert response.json()[0]["market"] == "NSE"


def test_delete_watchlist_stock(client):
    register_and_login(client)

    added = client.post(
        "/api/watchlist",
        json={"ticker": "WIPRO", "market": "NSE"},
        headers=csrf_headers(client)
    )

    assert added.status_code == 201

    stock_id = added.json()["saved_stock_id"]

    response = client.delete(
        f"/api/watchlist/{stock_id}",
        headers=csrf_headers(client)
    )

    assert response.status_code == 200

    watchlist = client.get("/api/watchlist")

    assert watchlist.status_code == 200
    assert watchlist.json() == []


def test_watchlist_add_requires_csrf(client):
    register_and_login(client)

    response = client.post(
        "/api/watchlist",
        json={"ticker": "TCS", "market": "BSE"}
    )

    assert response.status_code == 403


def test_watchlist_rejects_unsupported_market(client):
    register_and_login(client)

    response = client.post(
        "/api/watchlist",
        json={"ticker": "TCS", "market": "INVALID"},
        headers=csrf_headers(client)
    )

    assert response.status_code == 400


def test_watchlist_delete_cannot_access_another_users_stock(client):
    # User A creates a watchlist entry.
    register_and_login(client, "usera@example.com")

    added = client.post(
        "/api/watchlist",
        json={"ticker": "RELIANCE", "market": "NSE"},
        headers=csrf_headers(client)
    )

    assert added.status_code == 201
    stock_id = added.json()["saved_stock_id"]

    # User B logs in.
    client.post("/api/auth/logout", headers=csrf_headers(client))
    register_and_login(client, "userb@example.com")

    # User B must not delete User A's stock.
    response = client.delete(
        f"/api/watchlist/{stock_id}",
        headers=csrf_headers(client)
    )

    assert response.status_code == 404
