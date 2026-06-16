"""SQLAlchemy ORM models for sessions, reports, workflow events, and chat."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid4())


# Session lifecycle states.
STATUS_CREATED = "created"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


class ResearchSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_name: Mapped[str] = mapped_column(String(512))
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=STATUS_CREATED, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(),
    )

    report: Mapped[Report | None] = relationship(
        back_populates="session", uselist=False, cascade="all, delete-orphan",
    )
    events: Mapped[list[WorkflowEvent]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
    )
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan",
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, index=True,
    )
    # The full structured report (all required sections + sources).
    content: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[ResearchSession] = relationship(back_populates="report")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    # Integer autoincrement PK doubles as the strict insertion order for the SSE
    # replay/dedupe logic.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True,
    )
    node: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))  # running | completed | failed
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Intermediate output produced by the node (kept small / summarised).
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[ResearchSession] = relationship(back_populates="events")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True,
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[ResearchSession] = relationship(back_populates="messages")
