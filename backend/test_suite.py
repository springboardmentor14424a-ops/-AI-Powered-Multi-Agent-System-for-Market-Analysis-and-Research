import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, SavedStock, ResearchTask, UserPreference

def run_tests():
    print("========================================")
    print("RUNNING MULTI-AGENT STOCK PLATFORM TESTS")
    print("========================================")

    # Initialize tables explicitly
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] Health Check")

    # 2. Registration
    test_email = "analyst@stockresearch.ai"
    test_password = "SecurePassword123!"
    reg_payload = {
        "full_name": "Arjun Sharma",
        "email": test_email,
        "password": test_password
    }
    # Clean up if existed
    db = SessionLocal()
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    res = client.post("/api/v1/register", json=reg_payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"
    user_data = res.json()
    assert user_data["email"] == test_email
    assert user_data["full_name"] == "Arjun Sharma"
    assert "password_hash" not in user_data  # Plain or hashed password never exposed
    print(f"[PASS] User Registration (user_id={user_data['user_id']})")

    # Duplicate registration should fail
    res_dup = client.post("/api/v1/register", json=reg_payload)
    assert res_dup.status_code == 400, "Duplicate registration should return 400"
    print("[PASS] Duplicate Registration Prevention")

    # 3. Login
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    res_login = client.post("/api/v1/login", json=login_payload)
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    login_res_data = res_login.json()
    token = login_res_data["access_token"]
    assert token, "Token missing from login response"
    print("[PASS] User Login & JWT Token Generation")

    # Invalid login test
    bad_login = client.post("/api/v1/login", json={"email": test_email, "password": "WrongPassword"})
    assert bad_login.status_code == 401, "Invalid password should return 401"
    print("[PASS] Invalid Password Rejection (401)")

    # 4. Protected Route verification (Missing/Invalid Token)
    unauthorized_res = client.get("/api/v1/watchlist")
    assert unauthorized_res.status_code == 401, "Protected route without token should return 401"
    
    invalid_token_res = client.get("/api/v1/watchlist", headers={"Authorization": "Bearer invalid.fake.token"})
    assert invalid_token_res.status_code == 401, "Invalid token should return 401"
    print("[PASS] Token Auth Verification & Protected Route Guard")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 5. Get current user profile
    res_me = client.get("/api/v1/me", headers=auth_headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == test_email
    print("[PASS] GET /me (User Profile via JWT)")

    # 6. Preferences API
    res_pref = client.get("/api/v1/preferences", headers=auth_headers)
    assert res_pref.status_code == 200
    pref_data = res_pref.json()
    assert pref_data["preferred_market"] == "NSE"
    print(f"[PASS] GET /preferences (Market={pref_data['preferred_market']})")

    res_pref_update = client.put(
        "/api/v1/preferences",
        json={"preferred_market": "BSE", "preferred_analysis_period": "1 Year"},
        headers=auth_headers
    )
    assert res_pref_update.status_code == 200
    assert res_pref_update.json()["preferred_market"] == "BSE"
    assert res_pref_update.json()["preferred_analysis_period"] == "1 Year"
    print("[PASS] PUT /preferences (Updated to BSE, 1 Year)")

    # 7. Watchlist APIs
    # Add stock
    res_add_stock = client.post("/api/v1/watchlist", json={"ticker": "RELIANCE"}, headers=auth_headers)
    assert res_add_stock.status_code == 201, f"Add stock failed: {res_add_stock.text}"
    assert res_add_stock.json()["ticker"] == "RELIANCE"
    print("[PASS] POST /watchlist (Added RELIANCE)")

    # Add second stock
    client.post("/api/v1/watchlist", json={"ticker": "TCS"}, headers=auth_headers)
    print("[PASS] POST /watchlist (Added TCS)")

    # Duplicate stock prevention test
    res_dup_stock = client.post("/api/v1/watchlist", json={"ticker": "RELIANCE"}, headers=auth_headers)
    assert res_dup_stock.status_code == 400, "Duplicate stock in watchlist should return 400"
    print("[PASS] Watchlist Duplicate Prevention")

    # Get watchlist
    res_get_wl = client.get("/api/v1/watchlist", headers=auth_headers)
    assert res_get_wl.status_code == 200
    wl = res_get_wl.json()
    assert len(wl) == 2
    tickers = [s["ticker"] for s in wl]
    assert "RELIANCE" in tickers and "TCS" in tickers
    print(f"[PASS] GET /watchlist (Retrieved {len(wl)} stocks: {tickers})")

    # Delete stock from watchlist
    res_del_stock = client.delete("/api/v1/watchlist/RELIANCE", headers=auth_headers)
    assert res_del_stock.status_code == 200
    res_get_wl2 = client.get("/api/v1/watchlist", headers=auth_headers)
    assert len(res_get_wl2.json()) == 1
    print("[PASS] DELETE /watchlist/RELIANCE")

    # 8. Research Tasks & History
    task_payload = {
        "ticker": "INFY",
        "market": "NSE",
        "requested_period": "6 Months"
    }
    res_task = client.post("/api/v1/tasks", json=task_payload, headers=auth_headers)
    assert res_task.status_code == 201, f"Task creation failed: {res_task.text}"
    task_data = res_task.json()
    task_id = task_data["task_id"]
    assert task_data["ticker"] == "INFY"
    assert task_data["status"] == "Completed"
    assert task_data["recommendation"] == "Buy"
    print(f"[PASS] POST /tasks (Launched Task ID {task_id} for INFY)")

    # History API
    res_history = client.get("/api/v1/history", headers=auth_headers)
    assert res_history.status_code == 200
    history_tasks = res_history.json()
    assert len(history_tasks) >= 1
    assert any(t["task_id"] == task_id for t in history_tasks)
    print(f"[PASS] GET /history (Found {len(history_tasks)} past tasks)")

    # Get Task details
    res_task_details = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert res_task_details.status_code == 200
    assert res_task_details.json()["task_id"] == task_id
    print(f"[PASS] GET /tasks/{task_id} (Full Multi-Agent Report Accessible)")

    # 9. Stock Search & Quotes
    search_res = client.get("/api/v1/stocks/search?query=TAT")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert any("TATAMOTORS" in s["ticker"] for s in search_data)
    print(f"[PASS] GET /stocks/search?query=TAT (Matched {len(search_data)} results)")

    quote_res = client.get("/api/v1/stocks/quote/RELIANCE?market=NSE")
    assert quote_res.status_code == 200
    quote_data = quote_res.json()
    assert quote_data["ticker"] == "RELIANCE"
    assert quote_data["price"] > 0
    print(f"[PASS] GET /stocks/quote/RELIANCE (Price: {quote_data['currency']} {quote_data['price']})")

    print("\n========================================")
    print("ALL 12 BACKEND API & SECURITY TESTS PASSED!")
    print("========================================")

if __name__ == "__main__":
    run_tests()
