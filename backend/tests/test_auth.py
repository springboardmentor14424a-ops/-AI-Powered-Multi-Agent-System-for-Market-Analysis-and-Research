from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.security import hash_password, verify_password

client = TestClient(app)


def test_registration_validates_matching_passwords():
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Module One",
            "email": "module-one@example.com",
            "password": "strong-password",
            "confirm_password": "different-password",
        },
    )
    assert response.status_code == 422


def test_protected_route_requires_authentication():
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_password_hashing_supports_short_and_long_passwords():
    for password in ("strong-password", "a" * 100):
        password_hash = hash_password(password)
        assert password_hash.startswith("$bcrypt-sha256$")
        assert verify_password(password, password_hash)
        assert not verify_password(f"{password}wrong", password_hash)


def test_google_auth_is_unavailable_without_client_id(monkeypatch):
    monkeypatch.setattr(main.settings, "google_client_id", "")

    config = client.get("/api/auth/google/config")
    response = client.post("/api/auth/google", json={"credential": "x" * 30})

    assert config.status_code == 200
    assert config.json() == {"enabled": False, "client_id": ""}
    assert response.status_code == 503


def test_google_auth_rejects_invalid_id_token(monkeypatch):
    monkeypatch.setattr(main.settings, "google_client_id", "test-client-id")

    def reject_token(*_args, **_kwargs):
        raise ValueError("invalid token")

    monkeypatch.setattr(main.id_token, "verify_oauth2_token", reject_token)
    response = client.post("/api/auth/google", json={"credential": "x" * 30})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google sign-in credential"


def test_google_auth_requires_verified_email(monkeypatch):
    monkeypatch.setattr(main.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        main.id_token,
        "verify_oauth2_token",
        lambda *_args, **_kwargs: {
            "sub": "google-user-id",
            "email": "unverified@example.com",
            "email_verified": False,
        },
    )

    response = client.post("/api/auth/google", json={"credential": "x" * 30})

    assert response.status_code == 401
    assert response.json()["detail"] == "Google must provide a verified email address"


def test_google_auth_creates_verified_user_and_session(monkeypatch):
    monkeypatch.setattr(main.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        main.id_token,
        "verify_oauth2_token",
        lambda *_args, **_kwargs: {
            "sub": "google-user-id",
            "email": "researcher@example.com",
            "email_verified": True,
            "name": "Researcher",
        },
    )

    class FakeDatabase:
        user = None

        def scalar(self, _query):
            return self.user

        def add(self, instance):
            if isinstance(instance, main.User):
                self.user = instance

        def flush(self):
            self.user.user_id = 42

        def commit(self):
            pass

        def refresh(self, _instance):
            pass

    database = FakeDatabase()

    def override_database():
        yield database

    app.dependency_overrides[main.get_db] = override_database
    try:
        response = client.post("/api/auth/google", json={"credential": "x" * 30})
    finally:
        app.dependency_overrides.pop(main.get_db, None)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "researcher@example.com"
    assert response.json()["user"]["full_name"] == "Researcher"
    assert response.cookies.get("access_token") == response.json()["access_token"]
    assert database.user.password_hash.startswith("$bcrypt-sha256$")
