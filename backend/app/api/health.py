"""Health and readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "mock_mode": settings.mock_mode,
        "real_search": settings.use_real_search,
    }
