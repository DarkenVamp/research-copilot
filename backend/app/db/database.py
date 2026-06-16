"""Async SQLAlchemy engine, session factory, and schema bootstrap."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# Driver: psycopg 3 (the `postgresql+psycopg://` URL). Its async API is
# non-blocking on the event loop, and it's the single Postgres driver shared with
# the LangGraph checkpointer (which is psycopg-only) — so we don't pull in asyncpg.
# See docs/engineering-decisions.md §3.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """
    Apply Alembic migrations to head on startup.

    Alembic is the single source of truth for the app schema. The runner is
    synchronous, so it runs in a worker thread to avoid blocking the event loop.
    """
    from app.db.migrate import run_migrations  # noqa: PLC0415

    await asyncio.to_thread(run_migrations)


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency: yield a session, commit on success, roll back on error.

    Not wrapped in ``@asynccontextmanager`` — FastAPI consumes yield-dependencies
    as async generators directly; wrapping it would inject the context-manager
    object instead of the session.
    """
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Shared FastAPI dependency type for an injected DB session — used by all routers.
DbSession = Annotated[AsyncSession, Depends(get_db)]
