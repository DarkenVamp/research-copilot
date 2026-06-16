"""
Programmatic Alembic migration runner.

Lets the app apply migrations on startup (and the test suite apply them against a
fresh database) without shelling out to the Alembic CLI. Uses a synchronous
engine under the hood, so callers should run it in a worker thread when inside an
event loop (see ``app.db.database.init_db``).
"""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config

from alembic import command

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    return cfg


def run_migrations() -> None:
    """Upgrade the database to the latest revision."""
    command.upgrade(_alembic_config(), "head")
