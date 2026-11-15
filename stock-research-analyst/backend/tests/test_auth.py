from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from tests.conftest import login, register


def test_register_success_and_password_is_hashed(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@gmail.com"
    assert "password" not in body and "password_hash" not in body

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "alice@gmail.com"))
        assert user.password_hash != "Passw0rd123"
        assert user.password_hash.startswith("$2")  # bcrypt


def test_register_duplicate_email(client):
    register(client)
    r = register(client, email="ALICE@gmail.com")  # case-insensitive
    assert r.status_code == 409


def test_register_validation(client):
    bad_match = client.post(
        "/api/auth/register",
        json={"full_name": "Bob Test", "email": "bob@gmail.com", "password": "Passw0rd123", "confirm_password": "Other123"},
    )
    assert bad_match.status_code == 422
    assert register(client, email="bob@gmail.com", password="short1").status_code == 422
    assert register(client, email="bob@gmail.com", password="onlyletters").status_code == 422
    assert register(client, email="not-an-email").status_code == 422


def test_login_success_sets_http_only_cookie(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "alice@gmail.com", "password": "Passw0rd123"})
    assert r.status_code == 200
    set_cookie = r.headers.get_list("set-cookie")
    access = next(c for c in set_cookie if c.startswith("access_token="))
    assert "httponly" in access.lower()
    assert client.get("/api/auth/me").json()["email"] == "alice@gmail.com"


def test_login_wrong_password_and_unknown_email(client):
    register(client)
    wrong = client.post("/api/auth/login", json={"email": "alice@gmail.com", "password": "Wrong12345"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@gmail.com", "password": "Passw0rd123"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]  # no user enumeration


def test_protected_routes_require_login(client):
    for path in ("/api/auth/me", "/api/research", "/api/watchlist", "/api/preferences"):
        assert client.get(path).status_code == 401


def test_logout_clears_session(client):
    register(client)
    login(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_tampered_token_rejected(client):
    client.cookies.set("access_token", "not.a.valid.jwt")
    assert client.get("/api/auth/me").status_code == 401


def test_csrf_header_required_for_state_changes(client, alice):
    body = {"ticker": "AAPL", "market": "NASDAQ"}
    assert client.post("/api/watchlist", json=body).status_code == 403  # no header
    assert client.post("/api/watchlist", json=body, headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.post("/api/watchlist", json=body, headers=alice).status_code == 201
