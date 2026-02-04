from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.auth import AuthContext, get_auth_context
from app.db.session import get_session
from app.models.users import User
from app.schemas.users import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(auth: AuthContext = Depends(get_auth_context)) -> UserRead:
    if auth.actor_type != "user" or auth.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return UserRead.model_validate(auth.user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> UserRead:
    if auth.actor_type != "user" or auth.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    updates = payload.model_dump(exclude_unset=True)
    user: User = auth.user
    for key, value in updates.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)
