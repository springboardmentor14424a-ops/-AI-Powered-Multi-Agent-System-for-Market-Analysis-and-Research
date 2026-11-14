from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite is used only by the automated tests.
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
else:
    _engine_kwargs = {"pool_pre_ping": True}

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create missing tables, and apply the one in-place change older local databases need
    (social accounts have no password, so users.password_hash must allow NULL).
    For bigger schema changes later, move to Alembic migrations."""
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:  # harmless if the column is already nullable
            conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
