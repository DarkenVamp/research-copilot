"""Test configuration.

Spins up an ephemeral Postgres (via testcontainers) for the whole test session
and points the app at it, with mock mode forced (no API keys). Using real
Postgres means the tests exercise the JSONB columns and the AsyncPostgresSaver
checkpointer exactly as in production. The container is started before any app
module is imported so the cached Settings pick up DATABASE_URL.

Requires a running Docker daemon.
"""

from __future__ import annotations

import os

from testcontainers.postgres import PostgresContainer

os.environ["OPENAI_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""

# Match the production image (PG18 + pgvector) so behaviour is identical.
_postgres = PostgresContainer("pgvector/pgvector:pg18-trixie", driver="psycopg")
_postgres.start()
os.environ["DATABASE_URL"] = _postgres.get_connection_url()


def pytest_unconfigure(config) -> None:
    _postgres.stop()
