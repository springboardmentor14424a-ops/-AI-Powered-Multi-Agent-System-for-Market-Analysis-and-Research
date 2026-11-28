"""
smoke_test_fundamental_api.py
==============================
Real API smoke test for Fundamental Agent endpoint (POST /api/fundamental/analyze)
using live Yahoo Finance data and real JWT authentication.

Features tested:
  1. Backend server connectivity (/health)
  2. Authentication flow (/auth/signup and /auth/login)
  3. Real data analysis for TCS on NSE (INR)
  4. Real data analysis for AAPL on NASDAQ (USD)
  5. Strict JSON serialization (allow_nan=False)
  6. Verification of all 8 core analytical features
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

# Ensure working directory is backend and .env is loaded
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)

# Load environment variables from .env
env_file = BACKEND_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def http_request(url: str, method: str = "GET", headers: dict = None, json_body: dict = None, timeout: int = 60):
    """Simple HTTP client using standard library urllib."""
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req_headers = {"User-Agent": "FundamentalAgentSmokeTest/1.0"}
    if json_body is not None:
        req_headers["Content-Type"] = "application/json"
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_body = resp.read().decode("utf-8")
            status = resp.status
            try:
                parsed = json.loads(raw_body)
            except Exception:
                parsed = raw_body
            return status, parsed
    except urllib.error.HTTPError as err:
        raw_err = err.read().decode("utf-8")
        try:
            parsed_err = json.loads(raw_err)
        except Exception:
            parsed_err = raw_err
        return err.code, parsed_err
    except Exception as exc:
        return 0, {"error": str(exc)}


def ensure_backend_running():
    """Verify backend is reachable on port 8000, or start it if needed."""
    status, data = http_request(f"{API_BASE_URL}/health", timeout=2)
    if status == 200:
        print(f"[OK] Backend is already running and reachable at {API_BASE_URL}")
        return None

    print(f"Starting uvicorn server on {API_BASE_URL}...")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{BACKEND_DIR.parent}:{BACKEND_DIR}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=env,
    )

    # Wait up to 15 seconds for startup
    for i in range(15):
        time.sleep(1)
        status, data = http_request(f"{API_BASE_URL}/health", timeout=2)
        if status == 200:
            print(f"[OK] Backend server started successfully (PID: {proc.pid})")
            return proc

    proc.terminate()
    raise RuntimeError("Failed to start FastAPI backend within 15 seconds")


def authenticate():
    """Register or log in a smoke-test user to obtain a valid JWT token."""
    test_email = "fundamental_smoke_test@stockintel.com"
    test_password = "SmokeTestPassword123!"
    test_name = "Fundamental Smoke Tester"

    # Try signup
    signup_payload = {
        "full_name": test_name,
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password,
    }
    status, res = http_request(f"{API_BASE_URL}/auth/signup", method="POST", json_body=signup_payload)

    # If already exists (409) or created (201), proceed to login
    login_payload = {
        "email": test_email,
        "password": test_password,
    }
    status, res = http_request(f"{API_BASE_URL}/auth/login", method="POST", json_body=login_payload)

    if status != 200 or not isinstance(res, dict) or "access_token" not in res:
        raise RuntimeError(f"Authentication failed with status {status}: {res}")

    token = res["access_token"]
    print(f"[OK] Authenticated successfully. User: {test_email}, Token prefix: {token[:10]}...")
    return token


def verify_analysis_response(label: str, status: int, data: dict, expected_ticker: str, expected_market: str, expected_curr: str):
    """Deep verification of Fundamental Agent analysis response integrity."""
    print(f"\n==================================================")
    print(f"  VERIFYING: {label} ({expected_ticker} on {expected_market})")
    print(f"==================================================")

    checks = []

    # 1. HTTP Status
    checks.append(("HTTP Status 200", status == 200, f"Got {status}"))
    if status != 200:
        print(f"[FAIL] HTTP error: {data}")
        return False, checks

    # 2. Envelope fields
    checks.append(("success is True", data.get("success") is True, f"Got {data.get('success')}"))
    checks.append(("agent_name is Fundamental Agent", data.get("agent_name") == "Fundamental Agent", f"Got {data.get('agent_name')}"))
    checks.append(("ticker matches", data.get("ticker") == expected_ticker, f"Got {data.get('ticker')}"))
    checks.append(("market matches", data.get("market") == expected_market, f"Got {data.get('market')}"))
    checks.append(("company_name populated", bool(data.get("company_name")), f"Got {data.get('company_name')}"))
    checks.append(("currency matches", data.get("currency") == expected_curr, f"Got {data.get('currency')}"))
    checks.append(("market_price available", isinstance(data.get("market_price"), (int, float)) and data.get("market_price") > 0, f"Got {data.get('market_price')}"))
    checks.append(("reporting_periods available", bool(data.get("reporting_periods")), f"Got {len(data.get('reporting_periods', []))} periods"))

    # 3. Analysis object presence
    analysis = data.get("analysis", {})
    checks.append(("analysis object present", isinstance(analysis, dict), f"Type: {type(analysis)}"))

    # 4. Check all 8 analytical features
    rev_earn = analysis.get("revenue_earnings", [])
    checks.append(("Feature 1: Revenue & Earnings present", isinstance(rev_earn, list) and len(rev_earn) > 0, f"{len(rev_earn)} years"))

    profit = analysis.get("profitability", [])
    checks.append(("Feature 2: Profitability present", isinstance(profit, list) and len(profit) > 0, f"{len(profit)} years"))

    debt = analysis.get("debt_stability", [])
    checks.append(("Feature 3: Debt & Financial Stability present", isinstance(debt, list) and len(debt) > 0, f"{len(debt)} years"))

    ratios = analysis.get("financial_ratios", [])
    checks.append(("Feature 4: Financial Ratios present", isinstance(ratios, list) and len(ratios) > 0, f"{len(ratios)} years"))

    hist = analysis.get("historical_detail", [])
    checks.append(("Feature 5: Historical Performance detail present", isinstance(hist, list), f"{len(hist)} items"))

    dq = analysis.get("data_quality", {})
    checks.append(("Feature 7: Data Quality audit present", isinstance(dq, dict) and "issues" in dq, f"Issues: {len(dq.get('issues', []))}"))

    p_class = analysis.get("profitability_classification", {})
    checks.append(("Feature 8: Profitability Classification present", isinstance(p_class, dict) and "summary" in p_class, "Summary present"))

    # Feature 6 (Peer Comparison) defaults to None when peers not requested
    checks.append(("Feature 6: Peer Comparison field present", "peer_comparison" in analysis, f"Value: {analysis.get('peer_comparison')}"))

    # 5. Strict JSON Compliance (No NaN, Infinity, -Infinity)
    strict_json_ok = False
    try:
        raw_json = json.dumps(data, allow_nan=False)
        strict_json_ok = True
        no_nan_tokens = (": NaN" not in raw_json) and (": Infinity" not in raw_json)
        checks.append(("Strict JSON serializable (allow_nan=False)", strict_json_ok, "Passed"))
        checks.append(("Zero bare NaN / Infinity tokens", no_nan_tokens, "Passed"))
    except ValueError as ve:
        checks.append(("Strict JSON serializable (allow_nan=False)", False, str(ve)))

    # Print report table
    all_passed = True
    for name, passed, detail in checks:
        icon = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {icon} {name:45} -> {detail}")

    # Print summary highlights
    if all_passed:
        prof_summary = {item["Item"]: item["Value"] for item in p_class.get("summary", [])}
        print(f"\n  Company: {data.get('company_name')}")
        print(f"  Price: {data.get('currency')} {data.get('market_price')}")
        print(f"  Classification: {prof_summary.get('Overall Profitability Class', 'N/A')}")
        print(f"  Latest NPM: {prof_summary.get('Latest Net Profit Margin (%)', 'N/A')}")
        print(f"  Data Quality Status: {prof_summary.get('Data Quality Status', 'N/A')}")

    return all_passed, checks


def main():
    server_proc = None
    results = {}
    try:
        # Step 2: Ensure backend is running
        server_proc = ensure_backend_running()

        # Step 3: Authenticate
        token = authenticate()
        headers = {"Authorization": f"Bearer {token}"}

        # Step 4: Test A - TCS on NSE (Indian company)
        print("\nSending POST /api/fundamental/analyze for TCS (NSE)...")
        status_tcs, data_tcs = http_request(
            f"{API_BASE_URL}/api/fundamental/analyze",
            method="POST",
            headers=headers,
            json_body={"ticker": "TCS", "market": "NSE"},
        )
        tcs_passed, tcs_checks = verify_analysis_response("Test A: TCS (NSE)", status_tcs, data_tcs, "TCS", "NSE", "INR")
        results["TCS"] = {"status": status_tcs, "passed": tcs_passed, "data": data_tcs if tcs_passed else None}

        # Step 4: Test B - AAPL on NASDAQ (US company)
        print("\nSending POST /api/fundamental/analyze for AAPL (NASDAQ)...")
        status_aapl, data_aapl = http_request(
            f"{API_BASE_URL}/api/fundamental/analyze",
            method="POST",
            headers=headers,
            json_body={"ticker": "AAPL", "market": "NASDAQ"},
        )
        aapl_passed, aapl_checks = verify_analysis_response("Test B: AAPL (NASDAQ)", status_aapl, data_aapl, "AAPL", "NASDAQ", "USD")
        results["AAPL"] = {"status": status_aapl, "passed": aapl_passed, "data": data_aapl if aapl_passed else None}

        print("\n" + "="*50)
        print("  SMOKE TEST SUMMARY")
        print("="*50)
        print(f"  TCS (NSE):    {'PASSED' if tcs_passed else 'FAILED'} (HTTP {status_tcs})")
        print(f"  AAPL (NASDAQ):{'PASSED' if aapl_passed else 'FAILED'} (HTTP {status_aapl})")
        print("="*50)

        if not (tcs_passed and aapl_passed):
            sys.exit(1)

    except Exception as exc:
        print(f"\n[FATAL ERROR] Smoke test encountered an exception: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
    finally:
        if server_proc:
            print("Stopping spawned uvicorn server...")
            server_proc.terminate()


if __name__ == "__main__":
    main()
