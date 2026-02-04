from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field

from app.models.tenancy import TenantScoped


class Board(TenantScoped, table=True):
    __tablename__ = "boards"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    slug: str = Field(index=True)
    gateway_url: str | None = Field(default=None)
    gateway_token: str | None = Field(default=None)
    gateway_main_session_key: str | None = Field(default=None)
    gateway_workspace_root: str | None = Field(default=None)
    identity_template: str | None = Field(default=None)
    soul_template: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
