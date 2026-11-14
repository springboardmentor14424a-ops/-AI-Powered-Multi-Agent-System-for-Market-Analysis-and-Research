import requests
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("=================================================================")
    print("RUNNING TESTS: RESEARCH DELETE, STATUS TRACKING & WATCHLIST")
    print("=================================================================")

    # 1. Authenticate User A
    login_a = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "student.test@example.com",
        "password": "Password123!"
    })
    assert login_a.status_code == 200, f"User A login failed: {login_a.text}"
    cookies_a = login_a.cookies
    user_a = login_a.json()["user"]
    print(f"[User A Authenticated]: {user_a['email']} (ID: {user_a['user_id']})")

    # 2. Authenticate User B (Register if needed or login)
    user_b_email = "user.isolation.test@example.com"
    reg_b = requests.post(f"{BASE_URL}/auth/register", json={
        "full_name": "User Isolation Test",
        "email": user_b_email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    login_b = requests.post(f"{BASE_URL}/auth/login", json={
        "email": user_b_email,
        "password": "Password123!"
    })
    assert login_b.status_code == 200, f"User B login failed: {login_b.text}"
    cookies_b = login_b.cookies
    user_b = login_b.json()["user"]
    print(f"[User B Authenticated]: {user_b['email']} (ID: {user_b['user_id']})")

    # -------------------------------------------------------------
    # FEATURE 2: Research Status Tracking
    # -------------------------------------------------------------
    print("\n--- Testing Feature 2: Research Status Tracking ---")
    # Start task for User A
    task_res = requests.post(f"{BASE_URL}/tasks", json={
        "ticker": "AAPL",
        "market": "NASDAQ",
        "requested_period": "1 Month"
    }, cookies=cookies_a)
    assert task_res.status_code == 201, f"Task creation failed: {task_res.text}"
    task_a = task_res.json()
    task_id_a = task_a["task_id"]
    print(f" -> Task created for User A: ID={task_id_a}, Status={task_a['status']}")
    assert task_a["status"] in ["Pending", "Processing", "Completed"], f"Unexpected status: {task_a['status']}"

    # Test PATCH status endpoint
    for status_val in ["Pending", "Processing", "Completed", "Failed"]:
        patch_res = requests.patch(f"{BASE_URL}/tasks/{task_id_a}/status", json={"status": status_val}, cookies=cookies_a)
        assert patch_res.status_code == 200, f"Failed to patch status to {status_val}: {patch_res.text}"
        assert patch_res.json()["status"] == status_val
        print(f" -> Status updated and verified in DB: {status_val}")

    # Test invalid status rejection
    invalid_patch = requests.patch(f"{BASE_URL}/tasks/{task_id_a}/status", json={"status": "UnknownStatus"}, cookies=cookies_a)
    assert invalid_patch.status_code == 422, "Invalid status must be rejected with 422"
    print(" -> Invalid status correctly rejected with HTTP 422.")

    # -------------------------------------------------------------
    # FEATURE 1: Research History - Individual Delete Option
    # -------------------------------------------------------------
    print("\n--- Testing Feature 1: Research History Individual Delete & User Isolation ---")
    # Create another task for User A so we can delete one and keep the other
    task2_res = requests.post(f"{BASE_URL}/tasks", json={
        "ticker": "MSFT",
        "market": "NASDAQ",
        "requested_period": "3 Months"
    }, cookies=cookies_a)
    task2_id = task2_res.json()["task_id"]
    print(f" -> Second task created for User A: ID={task2_id}")

    # User B attempts to delete User A's task (must be blocked!)
    unauth_delete = requests.delete(f"{BASE_URL}/tasks/{task_id_a}", cookies=cookies_b)
    assert unauth_delete.status_code in [403, 404], f"Cross-user delete must be forbidden! Got: {unauth_delete.status_code}"
    print(" -> Data Isolation Verified: User B cannot delete User A's research task (HTTP 404/Unauthorized).")

    # User A deletes their own task
    del_res = requests.delete(f"{BASE_URL}/tasks/{task_id_a}", cookies=cookies_a)
    assert del_res.status_code == 204, f"Delete failed: {del_res.status_code}"
    print(f" -> User A successfully deleted task {task_id_a} (HTTP 204 No Content).")

    # Confirm it is no longer returned in User A's history
    history_res = requests.get(f"{BASE_URL}/tasks", cookies=cookies_a)
    user_a_history_ids = [t["task_id"] for t in history_res.json()]
    assert task_id_a not in user_a_history_ids, "Deleted task still returned in history!"
    assert task2_id in user_a_history_ids, "Other task of user was deleted by mistake!"
    print(" -> Verified: Deleted entry permanently removed, other entries for User A remain intact.")

    # -------------------------------------------------------------
    # FEATURE 3: Stock Watchlist Management
    # -------------------------------------------------------------
    print("\n--- Testing Feature 3: Watchlist Add, View, Remove & Isolation ---")
    # Clean up INFY if present from prior tests
    requests.delete(f"{BASE_URL}/watchlist/INFY", cookies=cookies_a)

    # 3.A Add Stock to Watchlist
    add_w = requests.post(f"{BASE_URL}/watchlist", json={
        "ticker": "INFY",
        "company_name": "Infosys Limited",
        "market": "NSE"
    }, cookies=cookies_a)
    assert add_w.status_code == 201, f"Failed to add to watchlist: {add_w.text}"
    saved_stock = add_w.json()
    print(f" -> Stock added to watchlist: {saved_stock['ticker']} ({saved_stock['company_name']}, {saved_stock['market']})")

    # Prevent duplicate
    dup_w = requests.post(f"{BASE_URL}/watchlist", json={
        "ticker": "INFY",
        "company_name": "Infosys Limited",
        "market": "NSE"
    }, cookies=cookies_a)
    assert dup_w.status_code == 400, "Duplicate entry should be rejected with 400"
    print(f" -> Duplicate prevention verified: {dup_w.json().get('detail')}")

    # 3.B View Saved Stocks
    view_w = requests.get(f"{BASE_URL}/watchlist", cookies=cookies_a)
    assert view_w.status_code == 200
    w_items = view_w.json()
    infy_item = next((item for item in w_items if item["ticker"] == "INFY"), None)
    assert infy_item is not None, "INFY not found in watchlist"
    assert infy_item["market"] == "NSE"
    assert "created_at" in infy_item
    print(f" -> View Watchlist verified: Found {len(w_items)} saved stock(s) for User A. Date added: {infy_item['created_at']}")

    # Isolation check: User B's watchlist should NOT contain User A's stock
    view_b_w = requests.get(f"{BASE_URL}/watchlist", cookies=cookies_b)
    b_tickers = [item["ticker"] for item in view_b_w.json()]
    assert "INFY" not in b_tickers, "User B saw User A's saved stock in their watchlist!"
    print(" -> Data Isolation Verified: User B cannot view User A's watchlist.")

    # 3.C Remove Stock from Watchlist
    del_w = requests.delete(f"{BASE_URL}/watchlist/INFY", cookies=cookies_a)
    assert del_w.status_code == 204
    print(" -> Removed INFY from User A's watchlist (HTTP 204).")

    # Confirm removal
    view_w_after = requests.get(f"{BASE_URL}/watchlist", cookies=cookies_a)
    assert not any(item["ticker"] == "INFY" for item in view_w_after.json())
    print(" -> Verified: INFY successfully removed from User A's watchlist.")

    print("\n=================================================================")
    print("ALL SPECIFICATION TESTS PASSED SUCCESSFULLY 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
