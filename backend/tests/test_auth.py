from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.database import SessionLocal
from app.models import User

VALID = {
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "password": "Str0ngPassw0rd",
    "confirm_password": "Str0ngPassw0rd",
}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**VALID, **overrides})


def login(client, email=VALID["email"], password=VALID["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------- registration ----------

def test_register_success_stores_only_a_hash(client):
    r = register(client)
    assert r.status_code == 201
    assert "successful" in r.json()["message"].lower()
    assert "password" not in str(r.json()).lower().replace("registration", "")

    with SessionLocal() as db:
        user = db.query(User).one()
        assert user.email == "ada@example.com"
        assert user.password_hash != VALID["password"]
        assert user.password_hash.startswith("$2")  # bcrypt


def test_register_duplicate_email_rejected_case_insensitive(client):
    assert register(client).status_code == 201
    r = register(client, email="ADA@Example.com")
    assert r.status_code == 409
    assert "already registered" in r.json()["detail"]


def test_register_validation_errors(client):
    r = register(client, email="not-an-email")
    assert r.status_code == 422 and "email" in r.json()["errors"]

    r = register(client, password="short1A", confirm_password="short1A")
    assert "password" in r.json()["errors"]

    r = register(client, password="alllowercase1", confirm_password="alllowercase1")
    assert "uppercase" in r.json()["errors"]["password"]

    r = register(client, confirm_password="Different1Password")
    assert r.json()["errors"]["confirm_password"] == "Passwords do not match."

    r = register(client, password="A1" + "a" * 80, confirm_password="A1" + "a" * 80)
    assert "password" in r.json()["errors"]


# ---------- login ----------

def test_login_success_sets_secure_cookies(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == "ada@example.com"
    assert body["csrf_token"]

    cookies = [c.lower() for c in r.headers.get_list("set-cookie")]
    auth_cookie = next(c for c in cookies if c.startswith(settings.COOKIE_NAME))
    assert "httponly" in auth_cookie and "samesite=lax" in auth_cookie


def test_login_failures_use_one_generic_message(client):
    register(client)
    wrong_pw = login(client, password="WrongPassw0rd")
    unknown = login(client, email="nobody@example.com")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json()["detail"] == unknown.json()["detail"] == "Incorrect email or password."


# ---------- JWT ----------

def test_token_contains_no_sensitive_data(client):
    register(client)
    login(client)
    token = client.cookies.get(settings.COOKIE_NAME)
    claims = jwt.decode(token, options={"verify_signature": False})
    assert set(claims) == {"sub", "iat", "exp"}


def test_protected_route_requires_valid_token(client):
    assert client.get("/api/dashboard").status_code == 401

    register(client)
    login(client)
    r = client.get("/api/dashboard")
    assert r.status_code == 200 and "Ada Lovelace" in r.json()["message"]


def test_me_restores_session_with_csrf_token(client):
    register(client)
    login_csrf = login(client).json()["csrf_token"]
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json()["csrf_token"] == login_csrf


def _forge(sub, secret, exp_delta):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(sub), "iat": now, "exp": now + exp_delta}, secret, algorithm="HS256"
    )


def test_expired_token_rejected(client):
    register(client)
    client.cookies.set(settings.COOKIE_NAME, _forge(1, settings.JWT_SECRET, timedelta(minutes=-5)))
    assert client.get("/api/auth/me").status_code == 401


def test_token_signed_with_wrong_key_rejected(client):
    register(client)
    client.cookies.set(
        settings.COOKIE_NAME, _forge(1, "x" * 40, timedelta(minutes=5))
    )
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_session(client):
    register(client)
    login(client)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


# ---------- CSRF ----------

def test_cookie_auth_post_requires_csrf_header(client):
    register(client)
    csrf = login(client).json()["csrf_token"]

    assert client.post("/api/_test/echo").status_code == 403
    assert client.post("/api/_test/echo", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.post("/api/_test/echo", headers={"X-CSRF-Token": csrf}).status_code == 200


def test_bearer_token_works_without_csrf(client):
    register(client)
    login(client)
    token = client.cookies.get(settings.COOKIE_NAME)
    client.cookies.clear()
    r = client.post("/api/_test/echo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
