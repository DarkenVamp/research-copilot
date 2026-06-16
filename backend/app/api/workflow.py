"""Workflow execution endpoints: run, resume, live SSE stream, event history."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import repository as repo
from app.db.database import get_db
from app.db.models import STATUS_COMPLETED, STATUS_FAILED, STATUS_RUNNING
from app.schemas.api import WorkflowEventRead
from app.services.pubsub import pubsub
from app.services.workflow_runner import run_workflow

router = APIRouter(tags=["workflow"])

_TERMINAL = {"done", "error"}


async def _require_session(session_id: str, db: AsyncSession):
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/run", status_code=202)
async def run(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    session = await _require_session(session_id, db)
    if session.status == STATUS_RUNNING:
        raise HTTPException(status_code=409, detail="Workflow already running")
    asyncio.create_task(run_workflow(session_id))
    return {"status": "started", "session_id": session_id}


@router.post("/sessions/{session_id}/resume", status_code=202)
async def resume(session_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    session = await _require_session(session_id, db)
    if session.status == STATUS_RUNNING:
        raise HTTPException(status_code=409, detail="Workflow already running")
    asyncio.create_task(run_workflow(session_id, resume=True))
    return {"status": "resuming", "session_id": session_id}


@router.get("/sessions/{session_id}/events", response_model=list[WorkflowEventRead])
async def event_history(
    session_id: str, db: AsyncSession = Depends(get_db)
) -> list[WorkflowEventRead]:
    await _require_session(session_id, db)
    events = await repo.list_events(db, session_id)
    return [WorkflowEventRead.model_validate(e) for e in events]


@router.get("/sessions/{session_id}/stream")
async def stream(session_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Server-Sent Events stream of workflow progress.

    Subscribes first (so no live event is missed), replays any already-persisted
    events for late subscribers, then tails live events until a terminal event.
    """
    session = await _require_session(session_id, db)
    queue = pubsub.subscribe(session_id)
    seen: set[str] = set()

    # Snapshot of events that already happened (catch-up).
    persisted = await repo.list_events(db, session_id)
    already_terminal = session.status in (STATUS_COMPLETED, STATUS_FAILED)

    async def event_generator():
        try:
            for e in persisted:
                seen.add(e.id)
                yield {
                    "event": "node",
                    "data": WorkflowEventRead.model_validate(e).model_dump_json(),
                }
            if already_terminal:
                yield {"event": "done", "data": session.status}
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

                import json

                yield {"event": msg.get("type", "node"), "data": json.dumps(msg)}
                if msg.get("type") in _TERMINAL:
                    break
        finally:
            pubsub.unsubscribe(session_id, queue)

    return EventSourceResponse(event_generator())
