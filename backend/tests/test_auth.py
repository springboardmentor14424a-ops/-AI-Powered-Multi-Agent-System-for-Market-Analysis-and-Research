
from sqlalchemy.orm import sessionmaker

from app.models import User
from app.auth import verify_password


def test_successful_registration(client, test_engine):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "NEWUSER@EXAMPLE.COM",
            "password": "StrongPass123!"
        }
    )

    assert response.status_code == 201

    SessionLocal = sessionmaker(bind=test_engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == "newuser@example.com"
        ).first()

        assert user is not None
        assert user.full_name == "Test User"
        assert user.password_hash != "StrongPass123!"
        assert verify_password(
            "StrongPass123!",
            user.password_hash
        )
    finally:
        db.close()


def test_duplicate_registration(client):
    payload = {
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "password": "StrongPass123!"
    }

    first = client.post(
        "/api/auth/register",
        json=payload
    )

    second = client.post(
        "/api/auth/register",
        json=payload
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_registration(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "A",
            "email": "invalid-email",
            "password": "123"
        }
    )

    assert response.status_code == 422



def test_successful_login_sets_authentication_cookies(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Login Test",
            "email": "login@example.com",
            "password": "StrongPass123!"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongPass123!"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "csrf_token" in response.cookies

    assert response.cookies.get("access_token")


def test_login_with_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Login Test",
            "email": "wrongpass@example.com",
            "password": "StrongPass123!"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401



def test_current_user_without_login(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_current_user_after_login(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Protected User",
            "email": "protected@example.com",
            "password": "StrongPass123!"
        }
    )

    login = client.post(
        "/api/auth/login",
        json={
            "email": "protected@example.com",
            "password": "StrongPass123!"
        }
    )

    assert login.status_code == 200

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"


def test_logout_requires_csrf_and_succeeds_with_valid_token(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Logout User",
            "email": "logout@example.com",
            "password": "StrongPass123!"
        }
    )

    login = client.post(
        "/api/auth/login",
        json={
            "email": "logout@example.com",
            "password": "StrongPass123!"
        }
    )

    assert login.status_code == 200

    # Missing CSRF token must be rejected.
    missing_csrf = client.post("/api/auth/logout")

    assert missing_csrf.status_code == 403

    # Valid CSRF token must allow logout.
    csrf_token = client.cookies.get("csrf_token")

    logout = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token}
    )

    assert logout.status_code == 200

    # Access cookie should no longer authenticate the client.
    me = client.get("/api/auth/me")

    assert me.status_code == 401

