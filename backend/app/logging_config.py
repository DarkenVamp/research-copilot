"""
Logging configuration.

Deployed environments emit one JSON object per log line (via
``python-json-logger``) so output is greppable and ready for ingestion by any log
aggregator. Local development uses a plain, human-readable formatter instead —
JSON is just noise when you're reading the console yourself.
"""

from __future__ import annotations

import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def _build_formatter(environment: str) -> logging.Formatter:
    if environment == "local":
        return logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    # Renamed/added fields mirror the previous hand-rolled schema
    # (ts/level/logger/message). Any ``logger.*(..., extra={...})`` keys are
    # appended as their own fields, and exceptions land in ``exc_info`` — the
    # library namespaces custom fields against reserved LogRecord attributes, so
    # extras can be passed by their plain names.
    return JsonFormatter(
        "{levelname}{name}{message}",
        style="{",
        rename_fields={"levelname": "level", "name": "logger"},
        timestamp="ts",
    )


def configure_logging(level: str = "INFO", environment: str = "dev") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter(environment))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Quiet noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
