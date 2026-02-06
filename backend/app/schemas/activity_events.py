from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class ActivityEventRead(SQLModel):
    id: UUID
    event_type: str
    message: str | None
    agent_id: UUID | None
    task_id: UUID | None
    created_at: datetime


class ActivityTaskCommentFeedItemRead(SQLModel):
    id: UUID
    created_at: datetime
    message: str | None
    agent_id: UUID | None
    agent_name: str | None = None
    agent_role: str | None = None
    task_id: UUID
    task_title: str
    board_id: UUID
    board_name: str
