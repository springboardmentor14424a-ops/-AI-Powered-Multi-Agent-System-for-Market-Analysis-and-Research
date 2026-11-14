import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import oauth as oauth_mod
from ..config import settings
from ..database import get_db
from ..models import OAuthAccount, User
from ..session import start_session

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["social sign-in"])

_registry = None


def get_registry():
    global _registry
    if _registry is None:
        _registry = oauth_mod.build_oauth()
    return _registry


def _fail(reason: str) -> RedirectResponse:
    """Send the browser back to the login page with a short error code."""
    return RedirectResponse(f"{settings.PUBLIC_URL}/login?error={quote(reason)}", status_code=303)


@router.get("/providers")
def providers():
    """Which social buttons the frontend should show as usable."""
    on = oauth_mod.enabled_providers()
    return [
        {"id": p, "label": oauth_mod.LABELS[p], "enabled": p in on} for p in oauth_mod.PROVIDERS
    ]


@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    if provider not in oauth_mod.enabled_providers():
        return _fail("provider_not_configured")
    client = getattr(get_registry(), provider)
    if provider == "apple":
        client.client_secret = oauth_mod.apple_client_secret()
    return await client.authorize_redirect(request, oauth_mod.redirect_uri(provider))


async def _finish(provider: str, request: Request, db: Session):
    if provider not in oauth_mod.enabled_providers():
        return _fail("provider_not_configured")
    try:
        identity = await oauth_mod.fetch_identity(get_registry(), provider, request)
    except Exception:  # bad state, denied consent, expired code, network trouble ...
        log.warning("social sign-in failed for %s", provider, exc_info=True)
        return _fail("signin_failed")
    if not identity.subject:
        return _fail("signin_failed")

    link = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider, OAuthAccount.subject == identity.subject
        )
    )
    if link is not None:
        user_id = link.user_id
    else:
        # Never attach a new provider identity to an existing account just because the
        # email matches - that would let anyone who controls such an email take it over.
        if identity.email and db.scalar(select(User.id).where(User.email == identity.email)):
            return _fail("email_exists")
        email = identity.email or f"{provider}-{identity.subject}@users.invalid"
        name = identity.name or (identity.email or "").split("@")[0] or f"{oauth_mod.LABELS[provider]} user"
        user = User(full_name=name[:100], email=email, password_hash=None)
        db.add(user)
        try:
            db.flush()
            db.add(OAuthAccount(user_id=user.id, provider=provider, subject=identity.subject, email=identity.email))
            db.commit()
        except IntegrityError:
            db.rollback()
            return _fail("signin_failed")
        user_id = user.id

    response = RedirectResponse(f"{settings.PUBLIC_URL}/dashboard", status_code=303)
    start_session(response, user_id)
    return response


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    return await _finish(provider, request, db)


@router.post("/oauth/{provider}/callback")
async def oauth_callback_post(provider: str, request: Request, db: Session = Depends(get_db)):
    """Apple returns its result as a form POST. Authlib reads code/state from the form."""
    if provider == "apple":
        form = await request.form()
        request.state.apple_user = form.get("user")
    return await _finish(provider, request, db)
