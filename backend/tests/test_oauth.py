import pytest
from sqlalchemy import select

from app import oauth as oauth_mod
from app.config import settings
from app.database import SessionLocal
from app.models import OAuthAccount, User
from app.oauth import Identity, identity_from_claims
from app.routers import oauth as oauth_router


@pytest.fixture()
def google_on(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "gid")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "gsecret")
    monkeypatch.setattr(oauth_router, "_registry", None)


def fake_identity(monkeypatch, ident):
    async def fake(oauth, provider, request):
        return ident

    monkeypatch.setattr(oauth_mod, "fetch_identity", fake)


def test_providers_list_shows_which_are_configured(client, google_on):
    data = {p["id"]: p["enabled"] for p in client.get("/api/auth/providers").json()}
    assert data == {"google": True, "microsoft": False, "apple": False, "x": False}


def test_unconfigured_provider_redirects_with_message(client):
    r = client.get("/api/auth/oauth/apple/login", follow_redirects=False)
    assert r.status_code == 303 and "error=provider_not_configured" in r.headers["location"]


def test_login_redirects_to_google_with_state_and_nonce(client, google_on):
    r = client.get("/api/auth/oauth/google/login", follow_redirects=False)
    loc = r.headers["location"]
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "state=" in loc and "nonce=" in loc and "client_id=gid" in loc
    assert "callback" in loc


def test_forged_state_is_rejected(client, google_on):
    r = client.get("/api/auth/oauth/google/callback?code=x&state=forged", follow_redirects=False)
    assert "error=signin_failed" in r.headers["location"]
    assert "access_token" not in r.cookies


def test_new_user_is_created_and_signed_in(client, google_on, monkeypatch):
    fake_identity(monkeypatch, Identity("google", "g-1", "ana@example.com", "Ana"))
    r = client.get("/api/auth/oauth/google/callback?code=x&state=y", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/dashboard")
    me = client.get("/api/auth/me").json()
    assert me["user"]["email"] == "ana@example.com" and me["user"]["full_name"] == "Ana"
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == "ana@example.com"))
        assert u.password_hash is None
        assert db.scalar(select(OAuthAccount).where(OAuthAccount.user_id == u.id)).subject == "g-1"


def test_returning_user_gets_the_same_account(client, google_on, monkeypatch):
    fake_identity(monkeypatch, Identity("google", "g-1", "ana@example.com", "Ana"))
    client.get("/api/auth/oauth/google/callback?code=x&state=y", follow_redirects=False)
    first = client.get("/api/auth/me").json()["user"]["id"]
    client.post("/api/auth/logout")
    client.get("/api/auth/oauth/google/callback?code=x&state=y", follow_redirects=False)
    assert client.get("/api/auth/me").json()["user"]["id"] == first
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1


def test_existing_email_is_never_auto_linked(client, google_on, monkeypatch):
    client.post("/api/auth/register", json={"full_name": "Real Owner", "email": "ana@example.com", "password": "Str0ng!Passw0rd", "confirm_password": "Str0ng!Passw0rd"})
    fake_identity(monkeypatch, Identity("google", "attacker", "ana@example.com", "Mallory"))
    r = client.get("/api/auth/oauth/google/callback?code=x&state=y", follow_redirects=False)
    assert "error=email_exists" in r.headers["location"]
    assert client.get("/api/auth/me").status_code == 401
    with SessionLocal() as db:
        assert db.scalars(select(OAuthAccount)).all() == []


def test_social_only_account_cannot_password_login(client, google_on, monkeypatch):
    fake_identity(monkeypatch, Identity("google", "g-2", "bo@example.com", "Bo"))
    client.get("/api/auth/oauth/google/callback?code=x&state=y", follow_redirects=False)
    client.post("/api/auth/logout")
    for pw in ("", "anything", "Str0ng!Passw0rd"):
        r = client.post("/api/auth/login", json={"email": "bo@example.com", "password": pw or "x"})
        assert r.status_code == 401


def test_identity_without_email_gets_placeholder(client, monkeypatch):
    monkeypatch.setattr(settings, "X_CLIENT_ID", "x")
    monkeypatch.setattr(settings, "X_CLIENT_SECRET", "s")
    monkeypatch.setattr(oauth_router, "_registry", None)
    fake_identity(monkeypatch, Identity("x", "123", None, "Xavier"))
    client.get("/api/auth/oauth/x/callback?code=x&state=y", follow_redirects=False)
    assert client.get("/api/auth/me").json()["user"]["email"] == "x-123@users.invalid"


def test_claims_only_trust_verified_email():
    ok = identity_from_claims("google", {"sub": "1", "email": "A@B.com", "email_verified": True, "name": "A"})
    assert ok.email == "a@b.com"
    assert identity_from_claims("google", {"sub": "1", "email": "a@b.com", "email_verified": False}).email is None
    assert identity_from_claims("apple", {"sub": "1", "email": "a@b.com", "email_verified": "true"}).email == "a@b.com"
    assert identity_from_claims("microsoft", {"sub": "1", "email": "a@b.com", "email_verified": True}).email is None
    with pytest.raises(ValueError):
        identity_from_claims("google", {})


def test_apple_client_secret_is_a_valid_es256_jwt(monkeypatch):
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    for k, v in dict(APPLE_CLIENT_ID="com.x.web", APPLE_TEAM_ID="TEAM", APPLE_KEY_ID="KID", APPLE_PRIVATE_KEY=pem.replace("\n", "\\n")).items():
        monkeypatch.setattr(settings, k, v)
    token = oauth_mod.apple_client_secret()
    claims = jwt.decode(token, key.public_key(), algorithms=["ES256"], audience="https://appleid.apple.com")
    assert claims["iss"] == "TEAM" and claims["sub"] == "com.x.web"
    assert jwt.get_unverified_header(token)["kid"] == "KID"
