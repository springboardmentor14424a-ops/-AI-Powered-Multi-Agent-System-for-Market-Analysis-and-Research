
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath("backend"))

# Alembic configuration
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import database Base and engine
from app.database.database import Base, engine

# Import all models so Alembic can detect them
from app.models.user import User
from app.models.saved_stock import SavedStock
from app.models.user_preference import UserPreference
from app.models.research_task import ResearchTask

# Metadata containing all database models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""

    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
