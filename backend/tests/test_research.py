
def register_and_login(client, email="research@example.com"):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Research User",
            "email": email,
            "password": "StrongPass123!"
        }
    )

    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "StrongPass123!"
        }
    )


def test_create_research_task(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.post(
        "/api/research/tasks",
        json={
            "ticker": "RELIANCE",
            "market": "NSE",
            "requested_period": "1Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 201
    assert response.json()["ticker"] == "RELIANCE"
    assert response.json()["market"] == "NSE"
    assert response.json()["requested_period"] == "1Y"
    assert response.json()["status"] == "Pending"


def test_research_creation_requires_csrf(client):
    register_and_login(client)

    response = client.post(
        "/api/research/tasks",
        json={
            "ticker": "TCS",
            "market": "NSE",
            "requested_period": "3M"
        }
    )

    assert response.status_code == 403


def test_invalid_research_market(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.post(
        "/api/research/tasks",
        json={
            "ticker": "TCS",
            "market": "INVALID",
            "requested_period": "3M"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 400


def test_invalid_research_period(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    response = client.post(
        "/api/research/tasks",
        json={
            "ticker": "TCS",
            "market": "NSE",
            "requested_period": "10Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 400


def test_research_history(client):
    register_and_login(client)

    csrf = client.cookies.get("csrf_token")

    client.post(
        "/api/research/tasks",
        json={
            "ticker": "INFY",
            "market": "NSE",
            "requested_period": "6M"
        },
        headers={"X-CSRF-Token": csrf}
    )

    response = client.get("/api/research/history")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ticker"] == "INFY"
