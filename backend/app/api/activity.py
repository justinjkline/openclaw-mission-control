from __future__ import annotations

import asyncio
import json
from collections import deque
from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import asc, desc, func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import ActorContext, require_admin_auth, require_admin_or_agent
from app.core.auth import AuthContext
from app.core.time import utcnow
from app.db.pagination import paginate
from app.db.session import async_session_maker, get_session
from app.models.activity_events import ActivityEvent
from app.models.agents import Agent
from app.models.boards import Board
from app.models.tasks import Task
from app.schemas.activity_events import ActivityEventRead, ActivityTaskCommentFeedItemRead
from app.schemas.pagination import DefaultLimitOffsetPage

router = APIRouter(prefix="/activity", tags=["activity"])

SSE_SEEN_MAX = 2000


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized = normalized.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _agent_role(agent: Agent | None) -> str | None:
    if agent is None:
        return None
    profile = agent.identity_profile
    if not isinstance(profile, dict):
        return None
    raw = profile.get("role")
    if isinstance(raw, str):
        role = raw.strip()
        return role or None
    return None


def _feed_item(
    event: ActivityEvent,
    task: Task,
    board: Board,
    agent: Agent | None,
) -> ActivityTaskCommentFeedItemRead:
    return ActivityTaskCommentFeedItemRead(
        id=event.id,
        created_at=event.created_at,
        message=event.message,
        agent_id=event.agent_id,
        agent_name=agent.name if agent else None,
        agent_role=_agent_role(agent),
        task_id=task.id,
        task_title=task.title,
        board_id=board.id,
        board_name=board.name,
    )


async def _fetch_task_comment_events(
    session: AsyncSession,
    since: datetime,
    *,
    board_id: UUID | None = None,
) -> Sequence[tuple[ActivityEvent, Task, Board, Agent | None]]:
    statement = (
        select(ActivityEvent, Task, Board, Agent)
        .join(Task, col(ActivityEvent.task_id) == col(Task.id))
        .join(Board, col(Task.board_id) == col(Board.id))
        .outerjoin(Agent, col(ActivityEvent.agent_id) == col(Agent.id))
        .where(col(ActivityEvent.event_type) == "task.comment")
        .where(col(ActivityEvent.created_at) >= since)
        .where(func.length(func.trim(col(ActivityEvent.message))) > 0)
        .order_by(asc(col(ActivityEvent.created_at)))
    )
    if board_id is not None:
        statement = statement.where(col(Task.board_id) == board_id)
    return cast(
        Sequence[tuple[ActivityEvent, Task, Board, Agent | None]],
        list(await session.exec(statement)),
    )


@router.get("", response_model=DefaultLimitOffsetPage[ActivityEventRead])
async def list_activity(
    session: AsyncSession = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> DefaultLimitOffsetPage[ActivityEventRead]:
    statement = select(ActivityEvent)
    if actor.actor_type == "agent" and actor.agent:
        statement = statement.where(ActivityEvent.agent_id == actor.agent.id)
    statement = statement.order_by(desc(col(ActivityEvent.created_at)))
    return await paginate(session, statement)


@router.get(
    "/task-comments",
    response_model=DefaultLimitOffsetPage[ActivityTaskCommentFeedItemRead],
)
async def list_task_comment_feed(
    board_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    auth: AuthContext = Depends(require_admin_auth),
) -> DefaultLimitOffsetPage[ActivityTaskCommentFeedItemRead]:
    statement = (
        select(ActivityEvent, Task, Board, Agent)
        .join(Task, col(ActivityEvent.task_id) == col(Task.id))
        .join(Board, col(Task.board_id) == col(Board.id))
        .outerjoin(Agent, col(ActivityEvent.agent_id) == col(Agent.id))
        .where(col(ActivityEvent.event_type) == "task.comment")
        .where(func.length(func.trim(col(ActivityEvent.message))) > 0)
        .order_by(desc(col(ActivityEvent.created_at)))
    )
    if board_id is not None:
        statement = statement.where(col(Task.board_id) == board_id)

    def _transform(items: Sequence[Any]) -> Sequence[Any]:
        rows = cast(Sequence[tuple[ActivityEvent, Task, Board, Agent | None]], items)
        return [_feed_item(event, task, board, agent) for event, task, board, agent in rows]

    return await paginate(session, statement, transformer=_transform)


@router.get("/task-comments/stream")
async def stream_task_comment_feed(
    request: Request,
    board_id: UUID | None = Query(default=None),
    since: str | None = Query(default=None),
    auth: AuthContext = Depends(require_admin_auth),
) -> EventSourceResponse:
    since_dt = _parse_since(since) or utcnow()
    seen_ids: set[UUID] = set()
    seen_queue: deque[UUID] = deque()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        last_seen = since_dt
        while True:
            if await request.is_disconnected():
                break
            async with async_session_maker() as session:
                rows = await _fetch_task_comment_events(session, last_seen, board_id=board_id)
            for event, task, board, agent in rows:
                event_id = event.id
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                seen_queue.append(event_id)
                if len(seen_queue) > SSE_SEEN_MAX:
                    oldest = seen_queue.popleft()
                    seen_ids.discard(oldest)
                if event.created_at > last_seen:
                    last_seen = event.created_at
                payload = {"comment": _feed_item(event, task, board, agent).model_dump(mode="json")}
                yield {"event": "comment", "data": json.dumps(payload)}
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator(), ping=15)
