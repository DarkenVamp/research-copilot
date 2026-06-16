"""Alembic migration environment.

Uses the app's settings for the database URL and ``Base.metadata`` as the
autogenerate target. A synchronous psycopg engine is used (the ``postgresql+psycopg``
URL works for both sync and async), so migrations can run from the Alembic CLI or
programmatically from a thread at app startup without an event-loop clash.

The LangGraph checkpoint tables (``checkpoints``, ``checkpoint_*``) are managed by
``AsyncPostgresSaver.setup()``, not Alembic, so they are filtered out of
autogenerate via ``include_name``.
"""

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import models so every table registers on Base.metadata before autogenerate.
import app.db.models  # noqa: F401
from app.config import settings
from app.db.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def include_name(name, type_, parent_names):  # noqa: ARG001
    """Limit migrations to our app tables; ignore LangGraph checkpoint tables."""
    if type_ == "table":
        return name in target_metadata.tables or name == "alembic_version"
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_name=include_name,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
