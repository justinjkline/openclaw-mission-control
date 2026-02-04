from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class BoardBase(SQLModel):
    name: str
    slug: str
    gateway_url: str | None = None
    gateway_main_session_key: str | None = None
    gateway_workspace_root: str | None = None
    identity_template: str | None = None
    soul_template: str | None = None


class BoardCreate(BoardBase):
    gateway_token: str | None = None


class BoardUpdate(SQLModel):
    name: str | None = None
    slug: str | None = None
    gateway_url: str | None = None
    gateway_token: str | None = None
    gateway_main_session_key: str | None = None
    gateway_workspace_root: str | None = None
    identity_template: str | None = None
    soul_template: str | None = None


class BoardRead(BoardBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
