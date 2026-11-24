
def register_and_login(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Preference User",
            "email": "preferences@example.com",
            "password": "StrongPass123!"
        }
    )

    return client.post(
        "/api/auth/login",
        json={
            "email": "preferences@example.com",
            "password": "StrongPass123!"
        }
    )


def test_default_preferences(client):
    register_and_login(client)

    response = client.get("/api/preferences")

    assert response.status_code == 200
    assert response.json()["market"] == "NASDAQ"
    assert response.json()["research_period"] == "3M"


def test_update_preferences(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.put(
        "/api/preferences",
        json={
            "market": "NSE",
            "research_period": "1Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 200
    assert response.json()["market"] == "NSE"
    assert response.json()["research_period"] == "1Y"


def test_invalid_market_rejected(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.put(
        "/api/preferences",
        json={
            "market": "INVALID",
            "research_period": "1Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 400


def test_invalid_period_rejected(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.put(
        "/api/preferences",
        json={
            "market": "NSE",
            "research_period": "10Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 400


def test_preferences_update_requires_csrf(client):
    register_and_login(client)

    response = client.put(
        "/api/preferences",
        json={
            "market": "BSE",
            "research_period": "3M"
        }
    )

    assert response.status_code == 403
