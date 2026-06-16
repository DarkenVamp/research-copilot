"""
FastAPI application entry point.

Wires logging, CORS, request logging, a consistent error envelope, the database
bootstrap, and the LangGraph engine lifecycle. Routers are mounted under /api.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import chat, health, sessions, workflow
from app.config import settings
from app.db.database import init_db
from app.logging_config import configure_logging, get_logger
from app.services.engine import engine

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.log_level, settings.environment)
    logger.info(
        "starting up",
        extra={
            "mock_mode": settings.mock_mode,
            "real_search": settings.use_real_search,
        },
    )
    await init_db()
    await engine.startup()
    try:
        yield
    finally:
        await engine.shutdown()
        logger.info("shutting down")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "request_failed", "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception):
    logger.exception("unhandled error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


app.include_router(health.router)
app.include_router(sessions.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
