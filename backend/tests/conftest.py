"""Test configuration.

Points the app at a throwaway SQLite database and forces mock mode (no API keys)
so the whole stack — graph, persistence, and HTTP API — is exercised with zero
external dependencies. Environment is set before any app module is imported so the
cached Settings pick it up.
"""

from __future__ import annotations

import os
import pathlib

_TEST_DB = pathlib.Path(__file__).parent / "test.db"

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""

# Start from a clean database each test session.
for _suffix in ("", "-wal", "-shm"):
    _p = pathlib.Path(str(_TEST_DB) + _suffix)
    if _p.exists():
        _p.unlink()
