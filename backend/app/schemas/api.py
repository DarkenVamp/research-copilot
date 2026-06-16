"""Request/response models for the HTTP API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Imported at runtime (not under TYPE_CHECKING): Pydantic resolves this annotation
# when building SessionDetail.
from app.schemas.report import ResearchReport  # noqa: TC001


class SessionCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=512)
    website: str | None = Field(default=None, max_length=2048)
    objective: str = Field(min_length=1, description="What the user wants to achieve")


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_name: str
    website: str | None
    objective: str
    status: str
    error: str | None
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionRead):
    report: ResearchReport | None = None


class WorkflowEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node: str
    status: str
    message: str | None
    data: dict | None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    answer: str
    history: list[ChatMessageRead]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
