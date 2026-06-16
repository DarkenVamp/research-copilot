"""Session CRUD endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repository as repo
from app.db.database import get_db
from app.schemas.api import SessionCreate, SessionDetail, SessionRead
from app.schemas.report import ResearchReport

router = APIRouter(tags=["sessions"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/sessions", response_model=SessionRead, status_code=201)
async def create_session(payload: SessionCreate, db: DbSession) -> SessionRead:
    session = await repo.create_session(
        db,
        company_name=payload.company_name,
        website=payload.website,
        objective=payload.objective,
    )
    return SessionRead.model_validate(session)


@router.get("/sessions", response_model=list[SessionRead])
async def list_sessions(db: DbSession) -> list[SessionRead]:
    sessions = await repo.list_sessions(db)
    return [SessionRead.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, db: DbSession) -> SessionDetail:
    session = await repo.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    report_row = await repo.get_report(db, session_id)
    report = ResearchReport(**report_row.content) if report_row else None

    return SessionDetail(
        **SessionRead.model_validate(session).model_dump(),
        report=report,
    )
