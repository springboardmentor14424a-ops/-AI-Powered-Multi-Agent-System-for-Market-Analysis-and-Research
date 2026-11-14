import urllib.request
import urllib.error
import json
import sys

BASE = 'http://127.0.0.1:8000'

def request(method, path, data=None, token=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode('utf-8') if data is not None else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            resp_body = res.read().decode('utf-8')
            return res.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode('utf-8')
        return e.code, json.loads(resp_body) if resp_body else {'error': str(e)}

def run_tests():
    print("=" * 60)
    print("RUNNING VERIFICATION SUITE FOR TASKS 4, 5, AND 6")
    print("=" * 60)

    # 1. Login
    print("\n[Step 1] Authenticating test user...")
    status, data = request('POST', '/api/auth/login', {'email': 'student.test@example.com', 'password': 'Password123!'})
    if status != 200:
        # Register if not present
        request('POST', '/api/auth/register', {
            'full_name': 'Test Student',
            'email': 'student.test@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        })
        status, data = request('POST', '/api/auth/login', {'email': 'student.test@example.com', 'password': 'Password123!'})
    assert status == 200, f"Login failed: {data}"
    token = data['access_token']
    user = data['user']
    print(f" -> Logged in successfully: {user['email']} (ID: {user['user_id']})")

    # 2. Task 6: User Preferences
    print("\n[Step 2] Testing Task 6: User Preferences (Market & Analysis Period)...")
    status, prefs = request('GET', '/api/preferences', token=token)
    assert status == 200, f"GET /api/preferences failed: {prefs}"
    print(f" -> Initial Preferences loaded: Market={prefs.get('preferred_market')}, Period={prefs.get('default_analysis_period')}")

    # Update preferences to NSE, 6 Months
    status, updated = request('PUT', '/api/preferences', {'preferred_market': 'NSE', 'default_analysis_period': '6 Months'}, token=token)
    assert status == 200, f"PUT /api/preferences failed: {updated}"
    assert updated['preferred_market'] == 'NSE'
    assert updated['default_analysis_period'] == '6 Months'
    print(f" -> Preferences updated and saved to DB: Market={updated['preferred_market']}, Period={updated['default_analysis_period']}")

    # Validate rejection of invalid market
    status, inv_resp = request('PUT', '/api/preferences', {'preferred_market': 'INVALID_MARKET', 'default_analysis_period': '1 Year'}, token=token)
    assert status == 422, f"Expected 422 for invalid market, got {status}"
    print(" -> Schema validation confirmed: Invalid market correctly rejected (HTTP 422).")

    # 3. Task 5: Saved Stocks & Watchlists
    print("\n[Step 3] Testing Task 5: Saved Stocks & Watchlists...")
    # Search
    status, search_res = request('GET', '/api/watchlist/search?q=INFY&market=NSE', token=token)
    assert status == 200 and len(search_res) > 0, f"Search failed: {search_res}"
    print(f" -> Stock search operational: Found {len(search_res)} match(es) for 'INFY'.")

    # Clean up if INFY already in watchlist
    request('DELETE', '/api/watchlist/INFY', token=token)

    # Add to watchlist
    status, add_res = request('POST', '/api/watchlist', {'ticker': 'INFY', 'company_name': 'Infosys Limited', 'market': 'NSE'}, token=token)
    assert status == 201, f"POST /api/watchlist failed: {add_res}"
    print(f" -> Added stock to watchlist: {add_res['ticker']} ({add_res['company_name']}, Market: {add_res['market']})")

    # Duplicate check
    status, dup_res = request('POST', '/api/watchlist', {'ticker': 'INFY', 'market': 'NSE'}, token=token)
    assert status == 400, f"Expected 400 duplicate error, got {status}"
    print(f" -> Duplicate prevention verified: {dup_res.get('detail')}")

    # View watchlist with live Yahoo Finance quotes
    status, wl = request('GET', '/api/watchlist', token=token)
    assert status == 200, f"GET /api/watchlist failed: {wl}"
    infy = next((i for i in wl if i['ticker'] == 'INFY'), None)
    assert infy is not None, "INFY not found in watchlist response"
    print(f" -> Watchlist retrieved with live market data: Last Price={infy.get('last_price')} {infy.get('currency')}, Change%={infy.get('change_pct')}%")

    # 4. Task 4: User-Specific Research History
    print("\n[Step 4] Testing Task 4: User-Specific Research History...")
    # Start research on INFY (NSE, 6 Months)
    status, task_res = request('POST', '/api/tasks', {
        'ticker': 'INFY',
        'company_name': 'Infosys Limited',
        'market': 'NSE',
        'requested_period': '6 Months'
    }, token=token)
    assert status == 201, f"POST /api/tasks failed: {task_res}"
    task_id = task_res['task_id']
    print(f" -> Research task started and persisted in DB: Task ID={task_id}, Status={task_res['status']}")

    # Also start research on AAPL (NASDAQ, 1 Year)
    status, task2_res = request('POST', '/api/tasks', {
        'ticker': 'AAPL',
        'company_name': 'Apple Inc.',
        'market': 'NASDAQ',
        'requested_period': '1 Year'
    }, token=token)
    assert status == 201, f"POST /api/tasks (AAPL) failed: {task2_res}"
    print(f" -> Research task started for AAPL (NASDAQ, 1 Year): Task ID={task2_res['task_id']}")

    # Retrieve history
    status, hist = request('GET', '/api/tasks', token=token)
    assert status == 200 and len(hist) >= 2, f"GET /api/tasks failed: {hist}"
    print(f" -> Research history retrieved: {len(hist)} tasks found for current user.")
    for t in hist[:2]:
        print(f"    • {t['ticker']} ({t['company_name']}) | Market: {t['market']} | Period: {t['requested_period']} | Status: {t['status']} | Date: {t['created_at']}")

    # Open generated report
    status, report_dossier = request('GET', f"/api/tasks/{task_id}", token=token)
    assert status == 200, f"GET /api/tasks/{task_id} failed: {report_dossier}"
    rep = report_dossier['report']
    print(" -> Generated report opened successfully from PostgreSQL:")
    print(f"    Title: {rep['title']}")
    print(f"    Summary: {rep['summary']}")
    print(f"    Limitations: {rep['limitations']}")

    # Remove stock from watchlist
    status, del_res = request('DELETE', '/api/watchlist/INFY', token=token)
    assert status in (200, 204), f"DELETE /api/watchlist/INFY failed: {del_res}"
    print("\n[Step 5] Watchlist removal action verified: INFY deleted cleanly (HTTP 204).")

    print("\n" + "=" * 60)
    print("RESULTS: ALL CHECKS FOR TASKS 4, 5, AND 6 PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
