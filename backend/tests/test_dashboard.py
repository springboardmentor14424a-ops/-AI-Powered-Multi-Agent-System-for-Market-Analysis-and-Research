
def register_and_login(client, email):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Dashboard User",
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


def test_dashboard_initial_counts(client):
    register_and_login(client, "dashboard@example.com")

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json()["watchlist_count"] == 0
    assert response.json()["research_count"] == 0
    assert response.json()["completed_count"] == 0


def test_dashboard_counts_are_user_specific(client):
    register_and_login(client, "usera@example.com")

    csrf = client.cookies.get("csrf_token")

    client.post(
        "/api/research/tasks",
        json={
            "ticker": "RELIANCE",
            "market": "NSE",
            "requested_period": "1Y"
        },
        headers={"X-CSRF-Token": csrf}
    )

    first_dashboard = client.get("/api/dashboard")

    assert first_dashboard.json()["research_count"] == 1

    # Log out User A.
    client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf}
    )

    # Log in as User B.
    register_and_login(client, "userb@example.com")

    second_dashboard = client.get("/api/dashboard")

    assert second_dashboard.status_code == 200
    assert second_dashboard.json()["research_count"] == 0
    assert second_dashboard.json()["watchlist_count"] == 0
    assert second_dashboard.json()["completed_count"] == 0
