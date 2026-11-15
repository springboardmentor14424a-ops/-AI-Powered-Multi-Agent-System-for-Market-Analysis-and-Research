import os

# Must be set BEFORE the app is imported. Tests use an in-memory SQLite DB.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["RESEARCH_STUB_DELAY_SECONDS"] = "0"
os.environ["YAHOO_SEARCH_ENABLED"] = "false"  # tests never call the network

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def register(client, email="alice@gmail.com", password="Passw0rd123", name="Alice Test"):
    return client.post(
        "/api/auth/register",
        json={"full_name": name, "email": email, "password": password, "confirm_password": password},
    )


def login(client, email="alice@gmail.com", password="Passw0rd123"):
    """Logs in; returns headers containing the CSRF token for state-changing requests."""
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"X-CSRF-Token": r.json()["csrf_token"]}


@pytest.fixture()
def alice(client):
    register(client)
    return login(client)
