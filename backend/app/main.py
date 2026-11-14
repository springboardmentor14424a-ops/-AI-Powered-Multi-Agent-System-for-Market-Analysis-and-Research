from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import init_db
from .deps import get_current_user
from .models import User
from .routers import auth, oauth, preferences, research, stocks
from .schemas import UserOut
from .workflow import mark_interrupted_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates the users table if it doesn't exist. For schema changes later,
    # move to Alembic migrations.
    init_db()
    mark_interrupted_tasks()
    yield


app = FastAPI(title="Multi-Agent Stock Research Analyst API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", settings.CSRF_HEADER_NAME],
)


# Holds the short-lived OAuth state/nonce/PKCE values between the redirect to a provider
# and the callback. Apple returns via a cross-site POST, which needs SameSite=None (HTTPS only).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET,
    session_cookie="oauth_session",
    max_age=600,
    same_site="none" if settings.COOKIE_SECURE else "lax",
    https_only=settings.COOKIE_SECURE,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Return {field: message} so the React forms can show errors under each input."""
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc = [str(p) for p in err["loc"] if p != "body"]
        field = loc[-1] if loc else "body"
        if err["type"] == "missing":
            msg = "This field is required."
        elif field == "email":
            msg = "Enter a valid email address."
        elif err["type"] == "literal_error":
            msg = "Choose one of the available options."
        else:
            msg = err["msg"].removeprefix("Value error, ")
        errors.setdefault(field, msg)
    return JSONResponse(
        status_code=422,
        content={"detail": "Please correct the highlighted fields.", "errors": errors},
    )


app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(research.router)
app.include_router(stocks.router)
app.include_router(preferences.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(user: User = Depends(get_current_user)):
    """Example protected route; the research workspace will build on this."""
    return {
        "message": f"Welcome back, {user.full_name}!",
        "user": UserOut.model_validate(user),
    }
