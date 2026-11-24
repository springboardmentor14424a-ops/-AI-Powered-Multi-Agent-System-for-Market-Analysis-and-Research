
from logging.config import fileConfig

from alembic import context

from app.database import Base, engine, settings
import app.models  # Register all SQLAlchemy models


# Alembic configuration
config = context.config


# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata for migration autogeneration
target_metadata = Base.metadata


# --------------------------------------------------
# OFFLINE MIGRATIONS
# --------------------------------------------------

def run_migrations_offline() -> None:

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------
# ONLINE MIGRATIONS
# --------------------------------------------------

def run_migrations_online() -> None:

    with engine.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


# --------------------------------------------------
# EXECUTION
# --------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
