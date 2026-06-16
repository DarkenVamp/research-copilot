"""
Compiled-graph + Postgres checkpointer lifecycle.

Owns the LangGraph checkpointer and the compiled graph. The checkpointer is what
gives the workflow **recoverability**: every node transition is persisted under
``thread_id = session_id``, so an interrupted run can resume from its last
checkpoint. It runs on the same Postgres instance as the application data, on a
dedicated psycopg connection pool.
"""

from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import settings
from app.graph.builder import build_graph
from app.logging_config import get_logger

logger = get_logger("app.services.engine")


class Engine:
    def __init__(self) -> None:
        self._graph: CompiledStateGraph | None = None
        self.saver: AsyncPostgresSaver | None = None
        self._pool: AsyncConnectionPool | None = None

    @property
    def graph(self) -> CompiledStateGraph:
        if not self._graph:
            raise ValueError("Graph Not Compiled")
        return self._graph

    async def startup(self) -> None:
        self._pool = AsyncConnectionPool(
            conninfo=settings.checkpointer_dsn,
            max_size=10,
            open=False,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
                "prepare_threshold": 0,
            },
        )
        await self._pool.open(wait=True)
        self.saver = AsyncPostgresSaver(self._pool)  # type: ignore[arg-type] # AsyncConnectionPool is allowed
        await self.saver.setup()  # idempotent: creates checkpoint tables
        self._graph = build_graph(self.saver)
        logger.info("graph engine ready")

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        logger.info("graph engine shut down")


# Single instance shared via app lifespan.
engine = Engine()
