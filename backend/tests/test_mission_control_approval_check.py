from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.approval_task_links import ApprovalTaskLink
from app.models.approvals import Approval
from app.models.boards import Board
from app.models.gateways import Gateway
from app.models.organizations import Organization
from app.models.task_custom_fields import TaskCustomFieldDefinition, TaskCustomFieldValue
from app.models.tasks import Task
from app.services.github.mission_control_approval_check import (
    REQUIRED_ACTION_TYPES,
    evaluate_approval_gate_for_pr_url,
)


async def _make_engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.connect() as conn, conn.begin():
        await conn.run_sync(SQLModel.metadata.create_all)
    return engine


async def _make_session(engine: AsyncEngine) -> AsyncSession:
    return AsyncSession(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_approval_gate_no_task_linked_is_missing() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            session.add(
                TaskCustomFieldDefinition(
                    organization_id=org_id,
                    field_key="github_pr_url",
                    label="GitHub PR URL",
                    field_type="url",
                )
            )
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/1",
            )
            assert out.outcome == "missing"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_gate_multiple_tasks_is_multiple() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()
            task_id_1 = uuid4()
            task_id_2 = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            field = TaskCustomFieldDefinition(
                organization_id=org_id,
                field_key="github_pr_url",
                label="GitHub PR URL",
                field_type="url",
            )
            session.add(field)
            session.add(Task(id=task_id_1, board_id=board_id, title="t1", description="", status="inbox"))
            session.add(Task(id=task_id_2, board_id=board_id, title="t2", description="", status="inbox"))
            await session.commit()

            session.add(
                TaskCustomFieldValue(
                    task_id=task_id_1,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/2",
                )
            )
            session.add(
                TaskCustomFieldValue(
                    task_id=task_id_2,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/2",
                )
            )
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/2",
            )
            assert out.outcome == "multiple"
            assert len(out.task_ids) == 2
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_gate_pending_is_pending() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()
            task_id = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            field = TaskCustomFieldDefinition(
                organization_id=org_id,
                field_key="github_pr_url",
                label="GitHub PR URL",
                field_type="url",
            )
            session.add(field)
            session.add(Task(id=task_id, board_id=board_id, title="t", description="", status="inbox"))
            await session.commit()

            session.add(
                TaskCustomFieldValue(
                    task_id=task_id,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/3",
                )
            )
            approval = Approval(
                board_id=board_id,
                task_id=task_id,
                action_type=sorted(REQUIRED_ACTION_TYPES)[0],
                confidence=90,
                status="pending",
            )
            session.add(approval)
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/3",
            )
            assert out.outcome == "pending"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_gate_approved_is_success() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()
            task_id = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            field = TaskCustomFieldDefinition(
                organization_id=org_id,
                field_key="github_pr_url",
                label="GitHub PR URL",
                field_type="url",
            )
            session.add(field)
            session.add(Task(id=task_id, board_id=board_id, title="t", description="", status="review"))
            await session.commit()

            session.add(
                TaskCustomFieldValue(
                    task_id=task_id,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/4",
                )
            )
            approval = Approval(
                board_id=board_id,
                task_id=None,
                action_type=sorted(REQUIRED_ACTION_TYPES)[0],
                confidence=90,
                status="approved",
            )
            session.add(approval)
            await session.commit()

            session.add(ApprovalTaskLink(approval_id=approval.id, task_id=task_id))
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/4",
            )
            assert out.outcome == "success"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_gate_rejected_is_rejected() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()
            task_id = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            field = TaskCustomFieldDefinition(
                organization_id=org_id,
                field_key="github_pr_url",
                label="GitHub PR URL",
                field_type="url",
            )
            session.add(field)
            session.add(Task(id=task_id, board_id=board_id, title="t", description="", status="review"))
            await session.commit()

            session.add(
                TaskCustomFieldValue(
                    task_id=task_id,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/5",
                )
            )
            approval = Approval(
                board_id=board_id,
                task_id=task_id,
                action_type=sorted(REQUIRED_ACTION_TYPES)[0],
                confidence=90,
                status="rejected",
            )
            session.add(approval)
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/5",
            )
            assert out.outcome == "rejected"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_gate_non_qualifying_action_type_is_missing() -> None:
    engine = await _make_engine()
    try:
        async with await _make_session(engine) as session:
            org_id = uuid4()
            board_id = uuid4()
            gateway_id = uuid4()
            task_id = uuid4()

            session.add(Organization(id=org_id, name="org"))
            session.add(
                Gateway(
                    id=gateway_id,
                    organization_id=org_id,
                    name="gateway",
                    url="https://gateway.local",
                    workspace_root="/tmp/workspace",
                )
            )
            session.add(
                Board(
                    id=board_id,
                    organization_id=org_id,
                    name="board",
                    slug="board",
                    gateway_id=gateway_id,
                )
            )
            field = TaskCustomFieldDefinition(
                organization_id=org_id,
                field_key="github_pr_url",
                label="GitHub PR URL",
                field_type="url",
            )
            session.add(field)
            session.add(Task(id=task_id, board_id=board_id, title="t", description="", status="review"))
            await session.commit()

            session.add(
                TaskCustomFieldValue(
                    task_id=task_id,
                    task_custom_field_definition_id=field.id,
                    value="https://github.com/acme/repo/pull/6",
                )
            )
            # approval exists but wrong action_type
            session.add(
                Approval(
                    board_id=board_id,
                    task_id=task_id,
                    action_type="some_other_action",
                    confidence=50,
                    status="approved",
                )
            )
            await session.commit()

            out = await evaluate_approval_gate_for_pr_url(
                session,
                board_id=board_id,
                pr_url="https://github.com/acme/repo/pull/6",
            )
            assert out.outcome == "missing"
    finally:
        await engine.dispose()
