"""Social sign-in providers (Google, Microsoft, Apple, X) built on Authlib.

Endpoints are spelled out explicitly (no network discovery at start-up). A provider is
enabled only when its credentials are present in the environment.
"""
import time
from dataclasses import dataclass
from pathlib import Path

import jwt
from authlib.integrations.starlette_client import OAuth

from .config import settings

PROVIDERS = ("google", "microsoft", "apple", "x")
LABELS = {"google": "Google", "microsoft": "Microsoft", "apple": "Apple", "x": "X"}


@dataclass
class Identity:
    provider: str
    subject: str          # the provider's stable user id
    email: str | None     # only set when the provider vouches for it
    name: str | None


# ---- Apple needs a client secret that is itself a short-lived signed JWT ----------------

def _apple_private_key() -> str:
    if settings.APPLE_PRIVATE_KEY_PATH:
        return Path(settings.APPLE_PRIVATE_KEY_PATH).read_text()
    return settings.APPLE_PRIVATE_KEY.replace("\\n", "\n")


def apple_client_secret() -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": settings.APPLE_TEAM_ID,
            "iat": now,
            "exp": now + 600,
            "aud": "https://appleid.apple.com",
            "sub": settings.APPLE_CLIENT_ID,
        },
        _apple_private_key(),
        algorithm="ES256",
        headers={"kid": settings.APPLE_KEY_ID},
    )


def enabled_providers() -> list[str]:
    s = settings
    ok = {
        "google": s.GOOGLE_CLIENT_ID and s.GOOGLE_CLIENT_SECRET,
        "microsoft": s.MICROSOFT_CLIENT_ID and s.MICROSOFT_CLIENT_SECRET,
        "x": s.X_CLIENT_ID and s.X_CLIENT_SECRET,
        "apple": s.APPLE_CLIENT_ID and s.APPLE_TEAM_ID and s.APPLE_KEY_ID
        and (s.APPLE_PRIVATE_KEY or s.APPLE_PRIVATE_KEY_PATH),
    }
    return [p for p in PROVIDERS if ok[p]]


def redirect_uri(provider: str) -> str:
    return f"{settings.PUBLIC_URL}/api/auth/oauth/{provider}/callback"


def build_oauth() -> OAuth:
    """Registry of the enabled providers. Built per app start so env changes are picked up."""
    s = settings
    oauth = OAuth()
    on = enabled_providers()
    if "google" in on:
        oauth.register(
            "google",
            client_id=s.GOOGLE_CLIENT_ID,
            client_secret=s.GOOGLE_CLIENT_SECRET,
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            access_token_url="https://oauth2.googleapis.com/token",
            jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
            issuer="https://accounts.google.com",
            client_kwargs={"scope": "openid email profile"},
        )
    if "microsoft" in on:
        base = f"https://login.microsoftonline.com/{s.MICROSOFT_TENANT}"
        oauth.register(
            "microsoft",
            client_id=s.MICROSOFT_CLIENT_ID,
            client_secret=s.MICROSOFT_CLIENT_SECRET,
            authorize_url=f"{base}/oauth2/v2.0/authorize",
            access_token_url=f"{base}/oauth2/v2.0/token",
            jwks_uri=f"{base}/discovery/v2.0/keys",
            # No fixed issuer: with the "common" tenant the issuer differs per account.
            client_kwargs={"scope": "openid email profile"},
        )
    if "x" in on:
        oauth.register(
            "x",
            client_id=s.X_CLIENT_ID,
            client_secret=s.X_CLIENT_SECRET,
            authorize_url="https://twitter.com/i/oauth2/authorize",
            access_token_url="https://api.twitter.com/2/oauth2/token",
            api_base_url="https://api.twitter.com/2/",
            client_kwargs={
                "scope": "users.read tweet.read",
                "code_challenge_method": "S256",  # X requires PKCE
                "token_endpoint_auth_method": "client_secret_basic",
            },
        )
    if "apple" in on:
        oauth.register(
            "apple",
            client_id=s.APPLE_CLIENT_ID,
            client_secret=apple_client_secret(),  # refreshed per request, see router
            authorize_url="https://appleid.apple.com/auth/authorize",
            access_token_url="https://appleid.apple.com/auth/token",
            jwks_uri="https://appleid.apple.com/auth/keys",
            issuer="https://appleid.apple.com",
            client_kwargs={
                "scope": "name email",
                "response_mode": "form_post",  # Apple posts the result back to us
                "token_endpoint_auth_method": "client_secret_post",
            },
        )
    return oauth


# ---- Turning a provider's answer into an Identity ----------------------------------------

def identity_from_claims(provider: str, claims: dict, extra_name: str | None = None) -> Identity:
    """Pure function (easy to test): decide which claims we trust.

    Email is kept only when the provider says it is verified, because an unverified email
    must never be used to decide who someone is.
    """
    subject = str(claims.get("sub") or "")
    if not subject:
        raise ValueError("The provider did not return a user id.")

    verified = claims.get("email_verified")
    if isinstance(verified, str):
        verified = verified.lower() == "true"
    email = (claims.get("email") or "").strip().lower() or None
    if provider == "microsoft":
        # Microsoft's "email" claim is not guaranteed verified; treat it as unknown.
        email = None
    elif not verified:
        email = None

    name = (claims.get("name") or extra_name or "").strip() or None
    return Identity(provider=provider, subject=subject, email=email, name=name)


async def fetch_identity(oauth: OAuth, provider: str, request, ) -> Identity:
    """Complete the code exchange and return who the user is."""
    client = getattr(oauth, provider)
    if provider == "apple":
        client.client_secret = apple_client_secret()
    token = await client.authorize_access_token(request)

    if provider == "x":
        resp = await client.get("users/me", token=token)
        resp.raise_for_status()
        data = (resp.json() or {}).get("data") or {}
        return Identity(
            provider="x",
            subject=str(data.get("id") or ""),
            email=None,  # X does not hand out a verified email
            name=(data.get("name") or data.get("username") or None),
        )

    # authorize_access_token has already verified the id_token (signature, issuer, audience,
    # expiry and the nonce stored in the session) and put its claims in token["userinfo"].
    claims = dict(token.get("userinfo") or {})
    if not claims:
        raise ValueError("The provider did not return an identity token.")
    extra_name = None
    if provider == "apple":  # Apple sends the name once, in the form post
        import json

        raw = getattr(request.state, "apple_user", None)
        if raw:
            try:
                n = json.loads(raw).get("name") or {}
                extra_name = f"{n.get('firstName', '')} {n.get('lastName', '')}".strip() or None
            except ValueError:
                pass
    return identity_from_claims(provider, claims, extra_name)
