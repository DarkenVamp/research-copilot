"""Workflow execution endpoints: run, resume, live SSE stream, event history."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import repository as repo
from app.db.database import DbSession, SessionLocal
from app.db.models import STATUS_COMPLETED, STATUS_FAILED, STATUS_RUNNING
from app.schemas.api import WorkflowEventRead
from app.services.pubsub import pubsub
from app.services.workflow_runner import run_workflow

router = APIRouter(tags=["workflow"])

_TERMINAL = {"done", "error"}

# Hold references to fire-and-forget workflow tasks so they are not
# garbage-collected mid-run (see ruff RUF006).
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro: Coroutine[Any, Any, None]) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _require_session(session_id: str, db: AsyncSession):
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/run", status_code=202)
async def run(session_id: str, db: DbSession) -> dict:
    session = await _require_session(session_id, db)
    if session.status == STATUS_RUNNING:
        raise HTTPException(status_code=409, detail="Workflow already running")
    _spawn(run_workflow(session_id))
    return {"status": "started", "session_id": session_id}


@router.post("/sessions/{session_id}/resume", status_code=202)
async def resume(session_id: str, db: DbSession) -> dict:
    session = await _require_session(session_id, db)
    if session.status == STATUS_RUNNING:
        raise HTTPException(status_code=409, detail="Workflow already running")
    _spawn(run_workflow(session_id, resume=True))
    return {"status": "resuming", "session_id": session_id}


@router.get("/sessions/{session_id}/events", response_model=list[WorkflowEventRead])
async def event_history(session_id: str, db: DbSession) -> list[WorkflowEventRead]:
    await _require_session(session_id, db)
    events = await repo.list_events(db, session_id)
    return [WorkflowEventRead.model_validate(e) for e in events]


async def _catchup_snapshot(
    session_id: str,
) -> tuple[list[tuple[int, str]], str | None]:
    """
    Validate the session and serialize already-persisted events for replay.

    Uses a short-lived session and serializes everything to JSON while it's open,
    so the (long-lived) SSE generator afterwards holds no DB connection. Returns
    the catch-up events plus the session's terminal status (or ``None`` if the
    run is still in flight and live events should be tailed).
    """
    async with SessionLocal() as db:
        session = await _require_session(session_id, db)
        catchup = [
            (e.id, WorkflowEventRead.model_validate(e).model_dump_json())
            for e in await repo.list_events(db, session_id)
        ]
    terminal = session.status in (STATUS_COMPLETED, STATUS_FAILED)
    return catchup, (session.status if terminal else None)


async def _progress_events(
    session_id: str,
    request: Request,
    queue: asyncio.Queue,
    catchup: list[tuple[int, str]],
    terminal_status: str | None,
):
    """Replay catch-up events, then tail live ones from the queue until terminal."""
    seen: set[int] = set()
    try:
        for event_id, data in catchup:
            seen.add(event_id)
            yield {"event": "node", "data": data}
        if terminal_status is not None:
            yield {"event": "done", "data": terminal_status}
            return

        while True:
            if await request.is_disconnected():
                break
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15)
            except TimeoutError:
                yield {"event": "ping", "data": "keepalive"}
                continue

            if msg.get("type") == "node" and msg.get("id") in seen:
                continue
            if msg.get("id"):
                seen.add(msg["id"])

            yield {"event": msg.get("type", "node"), "data": json.dumps(msg)}
            if msg.get("type") in _TERMINAL:
                break
    finally:
        pubsub.unsubscribe(session_id, queue)


@router.get("/sessions/{session_id}/stream")
async def stream(session_id: str, request: Request) -> EventSourceResponse:
    """
    Server-Sent Events stream of workflow progress.

    Subscribes first (so no live event is missed), replays any already-persisted
    events for late subscribers, then tails live events until a terminal event.
    """
    # Subscribe before the catch-up read so an event published in between isn't lost.
    queue = pubsub.subscribe(session_id)
    try:
        catchup, terminal_status = await _catchup_snapshot(session_id)
    except BaseException:
        pubsub.unsubscribe(session_id, queue)
        raise
    return EventSourceResponse(
        _progress_events(session_id, request, queue, catchup, terminal_status),
    )
