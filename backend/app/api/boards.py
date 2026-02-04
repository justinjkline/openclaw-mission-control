from __future__ import annotations

import asyncio
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlmodel import Session, col, select

from app.api.deps import (
    ActorContext,
    get_board_or_404,
    require_admin_auth,
    require_admin_or_agent,
)
from app.core.auth import AuthContext
from app.db.session import get_session
from app.integrations.openclaw_gateway import (
    GatewayConfig,
    OpenClawGatewayError,
    delete_session,
    ensure_session,
    send_message,
)
from app.models.activity_events import ActivityEvent
from app.models.agents import Agent
from app.models.boards import Board
from app.models.tasks import Task
from app.schemas.boards import BoardCreate, BoardRead, BoardUpdate

router = APIRouter(prefix="/boards", tags=["boards"])

AGENT_SESSION_PREFIX = "agent"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid4().hex


def _build_session_key(agent_name: str) -> str:
    return f"{AGENT_SESSION_PREFIX}:{_slugify(agent_name)}:main"


def _board_gateway_config(board: Board) -> GatewayConfig | None:
    if not board.gateway_url:
        return None
    if not board.gateway_main_session_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Board gateway_main_session_key is required",
        )
    if not board.gateway_workspace_root:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Board gateway_workspace_root is required",
        )
    return GatewayConfig(url=board.gateway_url, token=board.gateway_token)


async def _cleanup_agent_on_gateway(agent: Agent, board: Board, config: GatewayConfig) -> None:
    if agent.openclaw_session_id:
        await delete_session(agent.openclaw_session_id, config=config)
    if not board.gateway_main_session_key:
        raise OpenClawGatewayError("Board gateway_main_session_key is required")
    if not board.gateway_workspace_root:
        raise OpenClawGatewayError("Board gateway_workspace_root is required")
    main_session = board.gateway_main_session_key
    workspace_root = board.gateway_workspace_root
    workspace_path = f"{workspace_root.rstrip('/')}/workspace-{_slugify(agent.name)}"
    cleanup_message = (
        "Cleanup request for deleted agent.\n\n"
        f"Agent name: {agent.name}\n"
        f"Agent id: {agent.id}\n"
        f"Session key: {agent.openclaw_session_id or _build_session_key(agent.name)}\n"
        f"Workspace path: {workspace_path}\n\n"
        "Actions:\n"
        "1) Remove the workspace directory.\n"
        "2) Delete any lingering session artifacts.\n"
        "Reply NO_REPLY."
    )
    await ensure_session(main_session, config=config, label="Main Agent")
    await send_message(cleanup_message, session_key=main_session, config=config, deliver=False)


@router.get("", response_model=list[BoardRead])
def list_boards(
    session: Session = Depends(get_session),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> list[Board]:
    return list(session.exec(select(Board)))


@router.post("", response_model=BoardRead)
def create_board(
    payload: BoardCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(require_admin_auth),
) -> Board:
    data = payload.model_dump()
    if data.get("gateway_token") == "":
        data["gateway_token"] = None
    if data.get("identity_template") == "":
        data["identity_template"] = None
    if data.get("soul_template") == "":
        data["soul_template"] = None
    if data.get("gateway_url"):
        if not data.get("gateway_main_session_key"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="gateway_main_session_key is required when gateway_url is set",
            )
        if not data.get("gateway_workspace_root"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="gateway_workspace_root is required when gateway_url is set",
            )
    board = Board.model_validate(data)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.get("/{board_id}", response_model=BoardRead)
def get_board(
    board: Board = Depends(get_board_or_404),
    actor: ActorContext = Depends(require_admin_or_agent),
) -> Board:
    return board


@router.patch("/{board_id}", response_model=BoardRead)
def update_board(
    payload: BoardUpdate,
    session: Session = Depends(get_session),
    board: Board = Depends(get_board_or_404),
    auth: AuthContext = Depends(require_admin_auth),
) -> Board:
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("gateway_token") == "":
        updates["gateway_token"] = None
    if updates.get("identity_template") == "":
        updates["identity_template"] = None
    if updates.get("soul_template") == "":
        updates["soul_template"] = None
    for key, value in updates.items():
        setattr(board, key, value)
    if board.gateway_url:
        if not board.gateway_main_session_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="gateway_main_session_key is required when gateway_url is set",
            )
        if not board.gateway_workspace_root:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="gateway_workspace_root is required when gateway_url is set",
            )
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.delete("/{board_id}")
def delete_board(
    session: Session = Depends(get_session),
    board: Board = Depends(get_board_or_404),
    auth: AuthContext = Depends(require_admin_auth),
) -> dict[str, bool]:
    agents = list(session.exec(select(Agent).where(Agent.board_id == board.id)))
    task_ids = list(
        session.exec(select(Task.id).where(Task.board_id == board.id))
    )

    config = _board_gateway_config(board)
    if config:
        try:
            for agent in agents:
                asyncio.run(_cleanup_agent_on_gateway(agent, board, config))
        except OpenClawGatewayError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway cleanup failed: {exc}",
            ) from exc

    if task_ids:
        session.execute(
            delete(ActivityEvent).where(col(ActivityEvent.task_id).in_(task_ids))
        )
    if agents:
        agent_ids = [agent.id for agent in agents]
        session.execute(
            delete(ActivityEvent).where(col(ActivityEvent.agent_id).in_(agent_ids))
        )
        session.execute(delete(Agent).where(col(Agent.id).in_(agent_ids)))
    session.execute(delete(Task).where(col(Task.board_id) == board.id))
    session.delete(board)
    session.commit()
    return {"ok": True}
