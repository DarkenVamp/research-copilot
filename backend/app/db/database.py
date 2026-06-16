"""Async SQLAlchemy engine, session factory, and schema bootstrap."""

from __future__ import annotations

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


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """
    Create tables on startup.

    A real deployment would use Alembic migrations; create_all keeps the
    assignment runnable with a single command.
    """
    # Local import avoids a circular import (models import Base from this module).
    from app.db import models  # noqa: F401, PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
