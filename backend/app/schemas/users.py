from __future__ import annotations

from uuid import UUID

from sqlmodel import SQLModel


class UserBase(SQLModel):
    clerk_user_id: str
    email: str | None = None
    name: str | None = None
    preferred_name: str | None = None
    pronouns: str | None = None
    timezone: str | None = None
    notes: str | None = None
    context: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    name: str | None = None
    preferred_name: str | None = None
    pronouns: str | None = None
    timezone: str | None = None
    notes: str | None = None
    context: str | None = None


class UserRead(UserBase):
    id: UUID
    is_super_admin: bool
