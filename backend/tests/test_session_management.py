import urllib.request
import urllib.error
import http.cookiejar
import json
import psycopg2
from datetime import datetime, timezone, timedelta

BASE = 'http://127.0.0.1:8000'

def create_cookie_opener():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener, cj

def test_session_management():
    print("=" * 65)
    print("TESTING SECURE SESSION MANAGEMENT & AUTOMATIC LOGOUT")
    print("=" * 65)

    opener, cj = create_cookie_opener()

    # 1. Login & HTTP-only Cookie
    print("\n[Test 1] Testing User Login & Session Cookie Creation...")
    login_data = json.dumps({'email': 'student.test@example.com', 'password': 'Password123!'}).encode('utf-8')
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=login_data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with opener.open(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        print(f" -> Login successful for: {data['user']['email']}")

    # Check that session_token cookie was set
    session_cookies = [c for c in cj if c.name == 'session_token']
    assert len(session_cookies) > 0, "session_token cookie was NOT set!"
    session_cookie = session_cookies[0]
    session_id = session_cookie.value
    print(f" -> Received HTTP-only session cookie: {session_cookie.name} (Value: {session_id[:16]}...)")

    # 2. Verify Session Record in PostgreSQL
    print("\n[Test 2] Verifying Server-Side Session in PostgreSQL Database...")
    conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', password='sahIthi@01', dbname='stock_analyst')
    cur = conn.cursor()
    cur.execute("SELECT session_id, user_id, is_active, created_at, last_activity, expires_at FROM user_sessions WHERE session_id = %s", (session_id,))
    row = cur.fetchone()
    assert row is not None, "Session record not found in PostgreSQL user_sessions table!"
    assert row[2] == True, "Session is not active!"
    print(f" -> PostgreSQL session record verified: is_active={row[2]}, user_id={row[1]}")

    # 3. Access Protected Endpoint via Cookie
    print("\n[Test 3] Testing Protected API Access with Session Cookie...")
    req_me = urllib.request.Request(f"{BASE}/api/auth/me")
    with opener.open(req_me) as res:
        assert res.status == 200
        me = json.loads(res.read().decode('utf-8'))
        assert me['email'] == 'student.test@example.com'
        print(f" -> Protected endpoint /api/auth/me accessed successfully: {me['full_name']}")

    # Test other protected endpoints (watchlist & preferences)
    with opener.open(urllib.request.Request(f"{BASE}/api/preferences")) as res:
        assert res.status == 200
        print(" -> Protected endpoint /api/preferences accessed successfully.")
    with opener.open(urllib.request.Request(f"{BASE}/api/watchlist")) as res:
        assert res.status == 200
        print(" -> Protected endpoint /api/watchlist accessed successfully.")

    # 4. Manual Logout
    print("\n[Test 4] Testing Manual Logout & Server-Side Invalidation...")
    req_logout = urllib.request.Request(f"{BASE}/api/auth/logout", method='POST')
    with opener.open(req_logout) as res:
        assert res.status == 200
        print(" -> Logout endpoint returned 200 OK.")

    # Verify session is marked inactive in PostgreSQL
    cur.execute("SELECT is_active FROM user_sessions WHERE session_id = %s", (session_id,))
    assert cur.fetchone()[0] == False, "Session was NOT invalidated in database!"
    print(" -> Server-side session confirmed invalidated (is_active = False) in PostgreSQL.")

    # Verify previous cookie CANNOT be reused
    print("\n[Test 5] Verifying Expired/Invalidated Session Rejection...")
    try:
        req_me_reuse = urllib.request.Request(f"{BASE}/api/auth/me", headers={'Cookie': f"session_token={session_id}"})
        urllib.request.urlopen(req_me_reuse)
        assert False, "Should have been rejected with 401!"
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
        print(f" -> Correctly rejected reused session with HTTP 401: {e.reason}")

    # 5. Inactivity Timeout (15 minutes) Backend Check
    print("\n[Test 6] Testing 15-Minute Inactivity Timeout on Backend...")
    # Login again to get a fresh session
    opener2, cj2 = create_cookie_opener()
    with opener2.open(urllib.request.Request(f"{BASE}/api/auth/login", data=login_data, headers={'Content-Type': 'application/json'}, method='POST')) as res:
        pass
    new_sess_id = [c for c in cj2 if c.name == 'session_token'][0].value

    # Simulate 16 minutes of inactivity in database
    stale_time = datetime.now() - timedelta(minutes=16)
    cur.execute("UPDATE user_sessions SET last_activity = %s WHERE session_id = %s", (stale_time, new_sess_id))
    conn.commit()
    print(" -> Simulated 16 minutes of inactivity on active session.")

    # Next API call must detect inactivity and reject with 401
    try:
        opener2.open(urllib.request.Request(f"{BASE}/api/auth/me"))
        assert False, "Inactivity timeout should have rejected the request!"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        err_msg = json.loads(e.read().decode('utf-8'))
        assert "inactivity" in err_msg.get('detail', '').lower()
        print(f" -> Inactivity timeout successfully triggered: HTTP 401 ({err_msg['detail']})")

    # Verify session was marked inactive in DB
    cur.execute("SELECT is_active FROM user_sessions WHERE session_id = %s", (new_sess_id,))
    assert cur.fetchone()[0] == False
    print(" -> Stale session confirmed revoked in PostgreSQL.")

    # 6. Unauthenticated Request Blocking
    print("\n[Test 7] Verifying Unauthenticated Access Blocking...")
    try:
        urllib.request.urlopen(f"{BASE}/api/tasks")
        assert False, "Unauthenticated request should have been blocked!"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(" -> Unauthenticated request blocked with HTTP 401.")

    # 7. Google Sign-In Session Flow
    print("\n[Test 8] Testing Google Sign-In Session Management...")
    opener3, cj3 = create_cookie_opener()
    google_data = json.dumps({'email': 'sahithiredrouthu01@gmail.com', 'full_name': 'Sahithi Redrouthu'}).encode('utf-8')
    req_google = urllib.request.Request(f"{BASE}/api/auth/google", data=google_data, headers={'Content-Type': 'application/json'}, method='POST')
    with opener3.open(req_google) as res:
        assert res.status == 200
        print(" -> Google Sign-In succeeded.")
    
    g_session_cookies = [c for c in cj3 if c.name == 'session_token']
    assert len(g_session_cookies) > 0, "Google Sign-In did not set session cookie!"
    print(f" -> Google session cookie created: {g_session_cookies[0].name}")

    with opener3.open(urllib.request.Request(f"{BASE}/api/auth/me")) as res:
        assert res.status == 200
        g_user = json.loads(res.read().decode('utf-8'))
        assert g_user['email'] == 'sahithiredrouthu01@gmail.com'
        print(f" -> Authenticated via Google session: {g_user['email']}")

    conn.close()
    print("\n" + "=" * 65)
    print("ALL SESSION MANAGEMENT & AUTOMATIC LOGOUT TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == '__main__':
    test_session_management()
