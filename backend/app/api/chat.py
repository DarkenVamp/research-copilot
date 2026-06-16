"""Follow-up chat endpoints (grounded in the session's report)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.db import repository as repo
from app.db.database import (
    DbSession,
    SessionLocal,
)
from app.graph.chat_graph import astream_followup
from app.logging_config import get_logger
from app.schemas.api import ChatMessageRead, ChatRequest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

router = APIRouter(tags=["chat"])
logger = get_logger("app.api.chat")


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
async def list_messages(session_id: str, db: DbSession) -> list[ChatMessageRead]:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await repo.list_messages(db, session_id)
    return [ChatMessageRead.model_validate(m) for m in messages]


@router.post("/sessions/{session_id}/chat")
async def chat(
    session_id: str,
    payload: ChatRequest,
) -> EventSourceResponse:
    """
    Stream a follow-up answer over Server-Sent Events.

    Validation (404/409) happens up front so callers still get real HTTP status
    codes; the SSE stream then emits ``delta`` events as the answer is generated
    and a final ``done`` event. The user turn is persisted before streaming and
    the assistant turn once the answer is complete — both via a fresh session, so
    the writes don't depend on the request-scoped session's streaming lifecycle.
    """
    # Short-lived session for validation + grounding snapshot, released before the
    # stream so an open SSE connection doesn't pin a pooled DB connection. Snapshot
    # everything the generator needs as plain values while the session is open.
    async with SessionLocal() as db:
        if await repo.get_session(db, session_id) is None:
            raise HTTPException(status_code=404, detail="Session not found")

        report_row = await repo.get_report(db, session_id)
        if report_row is None:
            raise HTTPException(
                status_code=409,
                detail="No report yet — run the workflow before chatting.",
            )

        report = report_row.content
        prior = await repo.list_messages(db, session_id)
        history = [{"role": m.role, "content": m.content} for m in prior]
    question = payload.message

    async def event_generator() -> AsyncIterator[dict]:
        async with SessionLocal() as write_db:
            await repo.add_message(write_db, session_id, role="user", content=question)
            parts: list[str] = []
            try:
                async for delta in astream_followup(report, history, question):
                    parts.append(delta)
                    yield {"event": "delta", "data": json.dumps({"text": delta})}
                answer = "".join(parts)
                message = await repo.add_message(
                    write_db, session_id, role="assistant", content=answer,
                )
                yield {
                    "event": "done",
                    "data": ChatMessageRead.model_validate(message).model_dump_json(),
                }
            except Exception as exc:
                logger.exception("chat failed", extra={"session": session_id})
                yield {"event": "error", "data": json.dumps({"message": str(exc)})}

    return EventSourceResponse(event_generator())
