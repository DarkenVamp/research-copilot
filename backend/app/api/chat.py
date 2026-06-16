"""Follow-up chat endpoints (grounded in the session's report)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import repository as repo
from app.db.database import (
    DbSession,  # noqa: TC001 - runtime import: FastAPI resolves the dependency
)
from app.graph.chat_graph import answer_followup
from app.schemas.api import ChatMessageRead, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
async def list_messages(session_id: str, db: DbSession) -> list[ChatMessageRead]:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await repo.list_messages(db, session_id)
    return [ChatMessageRead.model_validate(m) for m in messages]


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: str,
    payload: ChatRequest,
    db: DbSession,
) -> ChatResponse:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    report_row = await repo.get_report(db, session_id)
    if report_row is None:
        raise HTTPException(
            status_code=409,
            detail="No report yet — run the workflow before chatting.",
        )

    # Prior turns become conversation context; the new question is passed separately.
    prior = await repo.list_messages(db, session_id)
    history = [{"role": m.role, "content": m.content} for m in prior]

    await repo.add_message(db, session_id, role="user", content=payload.message)
    answer = await answer_followup(report_row.content, history, payload.message)
    await repo.add_message(db, session_id, role="assistant", content=answer)

    messages = await repo.list_messages(db, session_id)
    return ChatResponse(
        answer=answer,
        history=[ChatMessageRead.model_validate(m) for m in messages],
    )
