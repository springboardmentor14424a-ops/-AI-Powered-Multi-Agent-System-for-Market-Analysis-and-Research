import pytest
import uuid

def test_user_registration(client):
    # 1. Successful registration
    payload = {
        "full_name": "Sahithi Redrouthu",
        "email": "sahithi@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "sahithi@example.com"
    assert data["full_name"] == "Sahithi Redrouthu"
    assert "user_id" in data
    assert "password" not in data
    assert "password_hash" not in data

    # 2. Reject mismatched passwords
    mismatch_payload = {
        "full_name": "Mismatch User",
        "email": "mismatch@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword123!"
    }
    mismatch_res = client.post("/api/auth/register", json=mismatch_payload)
    assert mismatch_res.status_code == 422

    # 3. Reject duplicate email
    duplicate_res = client.post("/api/auth/register", json=payload)
    assert duplicate_res.status_code == 400
    assert "already registered" in duplicate_res.json()["detail"]


def test_user_login_and_jwt_issuance(client):
    # 1. Invalid credentials
    invalid_login = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "WrongPassword!"
    })
    assert invalid_login.status_code == 401

    # 2. Valid credentials
    valid_login = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "Password123!"
    })
    assert valid_login.status_code == 200
    data = valid_login.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sahithi@example.com"


def test_protected_route_and_token_verification(client):
    # Unauthenticated request should fail with 401
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Authenticate and use token
    login_res = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    auth_res = client.get("/api/auth/me", headers=headers)
    assert auth_res.status_code == 200
    assert auth_res.json()["email"] == "sahithi@example.com"


def test_user_preferences_lifecycle(client):
    login_res = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch default preferences
    pref_res = client.get("/api/preferences", headers=headers)
    assert pref_res.status_code == 200
    assert pref_res.json()["preferred_market"] == "NASDAQ"
    assert pref_res.json()["default_analysis_period"] == "1 Year"

    # Update preferences to Indian market and 6 Months period
    update_res = client.put("/api/preferences", json={
        "preferred_market": "NSE",
        "default_analysis_period": "6 Months"
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["preferred_market"] == "NSE"
    assert update_res.json()["default_analysis_period"] == "6 Months"

    # Reject invalid market choice
    bad_res = client.put("/api/preferences", json={
        "preferred_market": "INVALID_EXCHANGE",
        "default_analysis_period": "1 Year"
    }, headers=headers)
    assert bad_res.status_code == 422


def test_watchlist_operations_and_duplicate_prevention(client):
    login_res = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search stocks
    search_res = client.get("/api/watchlist/search?q=AAPL", headers=headers)
    assert search_res.status_code == 200
    assert any(s["ticker"] == "AAPL" for s in search_res.json())

    # Add AAPL to watchlist
    add_res = client.post("/api/watchlist", json={
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "market": "NASDAQ"
    }, headers=headers)
    assert add_res.status_code == 201
    assert add_res.json()["ticker"] == "AAPL"

    # Prevent duplicate entry for same user and ticker
    dup_res = client.post("/api/watchlist", json={
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "market": "NASDAQ"
    }, headers=headers)
    assert dup_res.status_code == 400
    assert "already present in your watchlist" in dup_res.json()["detail"]

    # View watchlist
    list_res = client.get("/api/watchlist", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["ticker"] == "AAPL"

    # Delete stock from watchlist
    del_res = client.delete("/api/watchlist/AAPL", headers=headers)
    assert del_res.status_code == 204

    # Verify empty watchlist after delete
    empty_res = client.get("/api/watchlist", headers=headers)
    assert len(empty_res.json()) == 0


def test_research_tasks_and_user_data_isolation(client):
    # User 1
    u1_login = client.post("/api/auth/login", json={
        "email": "sahithi@example.com",
        "password": "Password123!"
    })
    u1_headers = {"Authorization": f"Bearer {u1_login.json()['access_token']}"}

    # User 2 (Fresh user to strictly test 0-task state and isolation)
    u2_email = f"analyst2_{uuid.uuid4().hex[:8]}@example.com"
    u2_register = client.post("/api/auth/register", json={
        "full_name": "Second Analyst",
        "email": u2_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert u2_register.status_code == 201

    u2_login = client.post("/api/auth/login", json={
        "email": u2_email,
        "password": "Password123!"
    })
    u2_headers = {"Authorization": f"Bearer {u2_login.json()['access_token']}"}

    # User 1 creates research task for TSLA
    t1_res = client.post("/api/tasks", json={
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "market": "NASDAQ",
        "requested_period": "1 Year"
    }, headers=u1_headers)
    assert t1_res.status_code == 201
    t1_id = t1_res.json()["task_id"]

    # User 1 history should contain TSLA
    u1_tasks = client.get("/api/tasks", headers=u1_headers)
    assert any(t["task_id"] == t1_id and t["ticker"] == "TSLA" for t in u1_tasks.json())

    # User 2 history must be completely empty (Strict Data Isolation)
    u2_tasks = client.get("/api/tasks", headers=u2_headers)
    assert len(u2_tasks.json()) == 0

    # User 2 cannot access User 1's task report
    u2_access_u1_task = client.get(f"/api/tasks/{t1_id}", headers=u2_headers)
    assert u2_access_u1_task.status_code == 404

    # User 1 can access their task report
    u1_report = client.get(f"/api/tasks/{t1_id}", headers=u1_headers)
    assert u1_report.status_code == 200
    assert u1_report.json()["report"]["title"].startswith("Initial Stock Research Summary: TSLA")


def test_continue_with_google_authentication(client):
    # 1. New user signs in with Google
    google_payload = {
        "email": "google.analyst@gmail.com",
        "full_name": "Google Analyst",
        "google_id": "google-oauth2-12345"
    }
    res = client.post("/api/auth/google", json=google_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "google.analyst@gmail.com"
    assert data["user"]["full_name"] == "Google Analyst"

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify protected route works with issued token
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "google.analyst@gmail.com"

    # 2. Existing user logs in again with Google
    res2 = client.post("/api/auth/google", json=google_payload)
    assert res2.status_code == 200
    assert res2.json()["user"]["email"] == "google.analyst@gmail.com"

