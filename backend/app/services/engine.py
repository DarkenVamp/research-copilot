"""Compiled-graph + checkpointer lifecycle.

Owns the LangGraph checkpointer and the compiled graph. The checkpointer is what
gives the workflow **recoverability**: every node transition is persisted under
``thread_id = session_id``, so an interrupted run can resume from its last
checkpoint.

Postgres is the production default (``AsyncPostgresSaver`` on a psycopg pool); a
``sqlite+aiosqlite`` ``DATABASE_URL`` transparently switches to
``AsyncSqliteSaver`` so the app runs in dev/test without a database server.
"""

from __future__ import annotations

from sqlalchemy.engine import make_url

from app.config import settings
from app.graph.builder import build_graph
from app.logging_config import get_logger

logger = get_logger("app.services.engine")


class Engine:
    def __init__(self) -> None:
        self.graph = None
        self.saver = None
        self._pool = None
        self._sqlite_conn = None

    async def startup(self) -> None:
        url = make_url(settings.database_url)
        backend = url.get_backend_name()

        if backend == "postgresql":
            await self._start_postgres()
        elif backend == "sqlite":
            await self._start_sqlite(url.database or ":memory:")
        else:
            raise RuntimeError(f"Unsupported database backend: {backend}")

        self.graph = build_graph(self.saver)
        logger.info("graph engine ready", extra={"ctx_backend": backend})

    async def _start_postgres(self) -> None:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool

        self._pool = AsyncConnectionPool(
            conninfo=settings.checkpointer_dsn,
            max_size=10,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row, "prepare_threshold": 0},
        )
        await self._pool.open(wait=True)
        self.saver = AsyncPostgresSaver(self._pool)
        await self.saver.setup()  # idempotent: creates checkpoint tables

    async def _start_sqlite(self, path: str) -> None:
        import aiosqlite
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        self._sqlite_conn = await aiosqlite.connect(path)
        self.saver = AsyncSqliteSaver(self._sqlite_conn)
        await self.saver.setup()

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        if self._sqlite_conn is not None:
            await self._sqlite_conn.close()
        logger.info("graph engine shut down")


# Single instance shared via app lifespan.
engine = Engine()
