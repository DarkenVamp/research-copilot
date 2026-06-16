"""
Data-access helpers.

These wrap all SQL so the API and workflow layers never build queries inline.
Relationships are fetched with explicit queries (not lazy loading), which is the
safe pattern under async SQLAlchemy.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    STATUS_CREATED,
    ChatMessage,
    Report,
    ResearchSession,
    WorkflowEvent,
)


# ---- Sessions ---------------------------------------------------------------
async def create_session(
    db: AsyncSession,
    *,
    company_name: str,
    website: str | None,
    objective: str,
) -> ResearchSession:
    session = ResearchSession(
        company_name=company_name,
        website=website,
        objective=objective,
        status=STATUS_CREATED,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> ResearchSession | None:
    return await db.get(ResearchSession, session_id)


async def list_sessions(db: AsyncSession) -> list[ResearchSession]:
    result = await db.execute(
        select(ResearchSession).order_by(ResearchSession.created_at.desc()),
    )
    return list(result.scalars().all())


async def update_session_status(
    db: AsyncSession,
    session_id: str,
    status: str,
    error: str | None = None,
) -> None:
    session = await db.get(ResearchSession, session_id)
    if session is None:
        return
    session.status = status
    session.error = error
    await db.commit()


# ---- Workflow events --------------------------------------------------------
async def add_event(  # noqa: PLR0913 - explicit event fields read better than a dict here
    db: AsyncSession,
    session_id: str,
    *,
    node: str,
    status: str,
    message: str | None = None,
    data: dict | None = None,
) -> WorkflowEvent:
    event = WorkflowEvent(
        session_id=session_id,
        node=node,
        status=status,
        message=message,
        data=data,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def list_events(db: AsyncSession, session_id: str) -> list[WorkflowEvent]:
    result = await db.execute(
        select(WorkflowEvent)
        .where(WorkflowEvent.session_id == session_id)
        .order_by(WorkflowEvent.id.asc()),
    )
    return list(result.scalars().all())


# ---- Reports ----------------------------------------------------------------
async def upsert_report(db: AsyncSession, session_id: str, content: dict) -> Report:
    existing = await get_report(db, session_id)
    if existing is not None:
        existing.content = content
        await db.commit()
        await db.refresh(existing)
        return existing
    report = Report(session_id=session_id, content=content)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_report(db: AsyncSession, session_id: str) -> Report | None:
    result = await db.execute(select(Report).where(Report.session_id == session_id))
    return result.scalar_one_or_none()


# ---- Chat -------------------------------------------------------------------
async def add_message(
    db: AsyncSession,
    session_id: str,
    *,
    role: str,
    content: str,
) -> ChatMessage:
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(db: AsyncSession, session_id: str) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc()),
    )
    return list(result.scalars().all())
