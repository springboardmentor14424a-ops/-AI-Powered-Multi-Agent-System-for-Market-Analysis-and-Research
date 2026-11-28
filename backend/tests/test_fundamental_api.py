"""
test_fundamental_api.py
========================
Dedicated API and router tests for the Fundamental Agent FastAPI endpoint
(POST /api/fundamental/analyze).

Test coverage:
  - 100% mocked dependencies (no live network or Yahoo Finance calls)
  - Authentication requirement (401 on missing/invalid token)
  - Valid ticker request with default market (NSE)
  - Multiple different tickers confirming dynamic execution (TCS, AAPL, RELIANCE)
  - Explicit market (NASDAQ, BSE)
  - Missing ticker field (422)
  - Empty or blank ticker (422)
  - Invalid ticker format (422)
  - Unsupported market (422)
  - Service failure / company not found (404)
  - Service provider failure without falsely reporting invalid ticker (502)
  - Unexpected internal exception handled gracefully (500)
  - Strict JSON compliance (allow_nan=False)
  - Alias route support (/fundamental/analyze)
"""

import asyncio
import json
import os
import unittest
from unittest.mock import MagicMock, patch
import uuid

# Set test environment variables before importing app
os.environ.setdefault("DATABASE_URL", "postgresql://test_user:test_pass@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_antigravity_123456789012")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id-12345")

from app.main import app
from app.core.security import get_current_user
from app.models.user import User


# ---------------------------------------------------------------------------
# IN-MEMORY ASGI TEST HELPER
# ---------------------------------------------------------------------------

async def call_asgi(app_instance, method: str, path: str, headers: dict = None, json_data: dict = None):
    """
    Executes an in-memory ASGI HTTP request against the FastAPI application.
    Does not require external HTTP client libraries, network sockets, or open ports.
    """
    body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
    h = [(b"host", b"testserver")]
    if headers:
        for k, v in headers.items():
            h.append((k.lower().encode("latin-1"), v.encode("latin-1")))
    if json_data is not None:
        h.append((b"content-type", b"application/json"))
        h.append((b"content-length", str(len(body)).encode("latin-1")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": h,
    }

    response_messages = []
    body_sent = False

    async def receive():
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        response_messages.append(message)

    await app_instance(scope, receive, send)

    status_code = None
    response_headers = {}
    response_body = bytearray()
    for msg in response_messages:
        if msg["type"] == "http.response.start":
            status_code = msg["status"]
            response_headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in msg.get("headers", [])}
        elif msg["type"] == "http.response.body":
            response_body.extend(msg.get("body", b""))

    try:
        data = json.loads(response_body.decode("utf-8")) if response_body else None
    except json.JSONDecodeError:
        data = response_body.decode("utf-8")

    return status_code, response_headers, data


class TestFundamentalAPI(unittest.TestCase):

    def setUp(self):
        # Create a mock authenticated user
        self.mock_user = MagicMock(spec=User)
        self.mock_user.user_id = uuid.uuid4()
        self.mock_user.email = "analyst@stockintel.com"
        self.mock_user.full_name = "Fundamental Analyst"
        self.mock_user.preferred_market = "NSE"

        # Synthetic successful analysis dictionary from service
        self.mock_service_success = {
            "success": True,
            "agent_name": "Fundamental Agent",
            "ticker": "TCS",
            "market": "NSE",
            "company_name": "Tata Consultancy Services Limited",
            "currency": "INR",
            "sector": "Technology",
            "industry": "Information Technology Services",
            "market_price": 3500.0,
            "retrieved_at": "2026-11-26T00:00:00+00:00",
            "data_source": "Yahoo Finance (mock)",
            "reporting_periods": ["2026-03-31", "2025-03-31"],
            "analysis": {
                "ticker": "TCS",
                "currency": "INR",
                "revenue_earnings": [
                    {"Financial_Year": "2025-03-31", "Revenue": 2400000000000.0, "Net_Income": 460000000000.0},
                    {"Financial_Year": "2026-03-31", "Revenue": 2650000000000.0, "Net_Income": 510000000000.0},
                ],
                "profitability": [
                    {"Financial_Year": "2026-03-31", "Net_Profit_Margin_%": 19.25, "Net_Margin_Status": "Improving"}
                ],
                "debt_stability": [
                    {"Financial_Year": "2026-03-31", "Debt_to_Equity": 0.08, "Current_Ratio": 2.45}
                ],
                "financial_ratios": [
                    {"Financial_Year": "2026-03-31", "ROE_%": 48.5, "PE_Ratio": 28.2, "PB_Ratio": 13.5}
                ],
                "historical_detail": [],
                "data_quality": {"issues": [], "critical_count": 0, "warning_count": 0, "info_count": 0},
                "profitability_classification": {
                    "summary": [
                        {"Item": "Company Ticker", "Value": "TCS"},
                        {"Item": "Overall Profitability Class", "Value": "Highly Profitable"},
                        {"Item": "Latest Net Profit Margin (%)", "Value": "19.25%"},
                    ]
                },
                "peer_comparison": None,
            },
        }

    def tearDown(self):
        # Clear FastAPI dependency overrides
        app.dependency_overrides.clear()

    # -----------------------------------------------------------------------
    # 1. Authentication Tests
    # -----------------------------------------------------------------------
    def test_unauthenticated_request_rejected(self):
        """Request without Authorization header must return 401 Unauthorized."""
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "TCS"})
        )
        self.assertEqual(status_code, 401)
        self.assertIn("detail", data)
        self.assertIn("Authentication required", data["detail"])

    def test_invalid_token_rejected(self):
        """Request with invalid Bearer token must return 401 Unauthorized."""
        headers = {"Authorization": "Bearer invalid_garbage_token"}
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", headers=headers, json_data={"ticker": "TCS"})
        )
        self.assertEqual(status_code, 401)
        self.assertIn("detail", data)
        self.assertIn("Invalid or expired token", data["detail"])

    # -----------------------------------------------------------------------
    # 2. Successful Analysis (Default and Explicit Markets)
    # -----------------------------------------------------------------------
    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_valid_ticker_default_market(self, mock_service):
        """Authenticated request with only ticker defaults market to NSE."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = self.mock_service_success

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "tcs"})
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["ticker"], "TCS")
        self.assertEqual(data["market"], "NSE")
        self.assertEqual(data["agent_name"], "Fundamental Agent")
        self.assertIn("analysis", data)
        self.assertEqual(
            data["analysis"]["profitability_classification"]["summary"][1]["Value"],
            "Highly Profitable",
        )
        mock_service.assert_called_once_with(ticker="TCS", market="NSE")

    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_different_ticker_nasdaq_market(self, mock_service):
        """Authenticated request with AAPL on NASDAQ confirms dynamic capability."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        aapl_result = dict(self.mock_service_success)
        aapl_result.update({
            "ticker": "AAPL",
            "market": "NASDAQ",
            "company_name": "Apple Inc.",
            "currency": "USD",
            "market_price": 225.0,
        })
        mock_service.return_value = aapl_result

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "AAPL", "market": "NASDAQ"})
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["ticker"], "AAPL")
        self.assertEqual(data["market"], "NASDAQ")
        self.assertEqual(data["currency"], "USD")
        mock_service.assert_called_once_with(ticker="AAPL", market="NASDAQ")

    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_explicit_market_bse(self, mock_service):
        """Authenticated request with explicit BSE market."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = dict(self.mock_service_success, ticker="500325", market="BSE")

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "500325", "market": "BSE"})
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(data["market"], "BSE")
        mock_service.assert_called_once_with(ticker="500325", market="BSE")

    # -----------------------------------------------------------------------
    # 3. Input Validation Errors
    # -----------------------------------------------------------------------
    def test_missing_ticker_rejected(self):
        """Payload without ticker field returns 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"market": "NSE"})
        )
        self.assertEqual(status_code, 422)

    def test_empty_ticker_rejected(self):
        """Blank or whitespace-only ticker returns 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "   "})
        )
        self.assertEqual(status_code, 422)

    def test_invalid_ticker_format_rejected(self):
        """Ticker with invalid symbols returns 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "INVALID!@#$"})
        )
        self.assertEqual(status_code, 422)

    def test_unsupported_market_rejected(self):
        """Market not in [NSE, BSE, NASDAQ, NYSE] returns 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "TCS", "market": "TOKYO"})
        )
        self.assertEqual(status_code, 422)

    # -----------------------------------------------------------------------
    # 4. Service Failures & Graceful Error Handling
    # -----------------------------------------------------------------------
    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_company_not_found_returns_404(self, mock_service):
        """When service reports company profile not found, endpoint returns 404."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = {
            "success": False,
            "error": "Company profile retrieval failed: Company profile not found for ticker 'UNKNOWN'",
            "ticker": "UNKNOWN",
            "market": "NSE",
            "agent_name": "Fundamental Agent",
        }

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "UNKNOWN"})
        )

        self.assertEqual(status_code, 404)
        self.assertFalse(data["success"])
        self.assertIn("Company profile not found", data["error"])
        self.assertEqual(data["ticker"], "UNKNOWN")

    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_service_provider_failure_returns_502(self, mock_service):
        """External provider timeout returns 502 without falsely claiming invalid ticker."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = {
            "success": False,
            "error": "Failed to retrieve financial statements: External provider timeout after 10s",
            "ticker": "RELIANCE",
            "market": "NSE",
            "agent_name": "Fundamental Agent",
        }

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "RELIANCE"})
        )

        self.assertEqual(status_code, 502)
        self.assertFalse(data["success"])
        self.assertIn("timeout", data["error"].lower())

    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_unexpected_internal_exception_returns_500(self, mock_service):
        """Unhandled internal error returns 500 without leaking stack traces."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.side_effect = RuntimeError("Fatal memory segmentation error in native C library")

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "TCS"})
        )

        self.assertEqual(status_code, 500)
        self.assertFalse(data["success"])
        self.assertIn("unexpected error occurred", data["error"])
        # Crucial security requirement: raw traceback MUST NOT be leaked to client
        self.assertNotIn("Fatal memory segmentation error", data["error"])

    # -----------------------------------------------------------------------
    # 5. Strict JSON Compliance & Alias Route Tests
    # -----------------------------------------------------------------------
    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_strict_json_serialization(self, mock_service):
        """Response must pass json.dumps(..., allow_nan=False) without ValueError."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = self.mock_service_success

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/api/fundamental/analyze", json_data={"ticker": "TCS"})
        )

        self.assertEqual(status_code, 200)
        # Verify strict JSON compliance
        serialized = json.dumps(data, allow_nan=False)
        self.assertIsInstance(serialized, str)
        self.assertNotIn(": NaN", serialized)
        self.assertNotIn(": Infinity", serialized)

    @patch("app.routers.fundamental.analyze_company_fundamentals")
    def test_alias_route_fundamental_analyze(self, mock_service):
        """Verifies /fundamental/analyze works identically as an alias."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        mock_service.return_value = self.mock_service_success

        status_code, _, data = asyncio.run(
            call_asgi(app, "POST", "/fundamental/analyze", json_data={"ticker": "TCS"})
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["ticker"], "TCS")


if __name__ == "__main__":
    unittest.main()
