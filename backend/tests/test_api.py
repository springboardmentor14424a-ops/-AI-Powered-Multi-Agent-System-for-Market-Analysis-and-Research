from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_ok():
    assert client.get("/").json() == {"status": "ok"}


def test_protected_routes_reject_missing_token():
    for path in ["/auth/me", "/watchlist", "/preferences", "/research", "/stocks/AAPL/history"]:
        assert client.get(path).status_code in (401, 403), path


def test_bad_token_rejected():
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_register_validation():
    r = client.post(
        "/auth/register",
        json={
            "full_name": "A B",
            "email": "not-an-email",
            "password": "short",
            "confirm_password": "different",
        },
    )
    assert r.status_code == 422