# API reference

## Deep dives

- [Architecture](05-architecture.md)
- [Gateway protocol](openclaw_gateway_ws.md)

This page summarizes the **HTTP API surface** exposed by the FastAPI backend.
It is derived from `backend/app/main.py` (router registration) and `backend/app/api/*` (route modules).

## Base
- API prefix: `/api/v1/*` (see `backend/app/main.py`)

## Auth model (recap)
- **Clerk (user auth)**: used by the human web UI; frontend enables Clerk when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set; backend verifies requests using `CLERK_SECRET_KEY` via the Clerk SDK (see `backend/app/core/auth.py`).
- **X-Agent-Token (agent auth)**: used by automation/agents; send header `X-Agent-Token: <token>` to `/api/v1/agent/*` endpoints (see `backend/app/core/agent_auth.py`).

## Route groups (modules)

| Module | Prefix (under `/api/v1`) | Purpose |
|---|---|---|
| `activity.py` | `/activity` | Activity listing and task-comment feed endpoints. |
| `agent.py` | `/agent` | Agent-scoped API routes for board operations and gateway coordination. |
| `agents.py` | `/agents` | Thin API wrappers for async agent lifecycle operations. |
| `approvals.py` | `/boards/{board_id}/approvals` | Approval listing, streaming, creation, and update endpoints. |
| `auth.py` | `/auth` | Authentication bootstrap endpoints for the Mission Control API. |
| `board_group_memory.py` | `/board-groups/{group_id}/memory` and `/boards/{board_id}/group-memory` | Board-group memory CRUD and streaming endpoints. |
| `board_groups.py` | `/board-groups` | Board group CRUD, snapshot, and heartbeat endpoints. |
| `board_memory.py` | `/boards/{board_id}/memory` | Board memory CRUD and streaming endpoints. |
| `board_onboarding.py` | `/boards/{board_id}/onboarding` | Board onboarding endpoints for user/agent collaboration. |
| `boards.py` | `/boards` | Board CRUD and snapshot endpoints. |
| `gateway.py` | `/gateways` | Thin gateway session-inspection API wrappers. |
| `gateways.py` | `/gateways` | Thin API wrappers for gateway CRUD and template synchronization. |
| `metrics.py` | `/metrics` | Dashboard metric aggregation endpoints. |
| `organizations.py` | `/organizations` | Organization management endpoints and membership/invite flows. |
| `souls_directory.py` | `/souls-directory` | API routes for searching and fetching souls-directory markdown entries. |
| `tasks.py` | `/boards/{board_id}/tasks` | Task API routes for listing, streaming, and mutating board tasks. |
| `users.py` | `/users` | User self-service API endpoints for profile retrieval and updates. |

## Backend API layer notes (how modules are organized)

Evidence: `backend/app/main.py`, `backend/app/api/*`, `backend/app/api/deps.py`.

### Conventions

- Each file under `backend/app/api/*` typically declares an `APIRouter` (`router = APIRouter(...)`) and defines endpoints with decorators like `@router.get(...)`, `@router.post(...)`, etc.
- Board-scoped modules embed `{board_id}` in the prefix (e.g. `/boards/{board_id}/tasks`).
- Streaming endpoints usually expose **SSE** endpoints at `.../stream` (see `sse-starlette` usage).

### Where key behaviors live

- **Router wiring / base prefix**: `backend/app/main.py` mounts these routers under `/api/v1/*`.
- **Auth / access control** is mostly expressed through dependencies (see `backend/app/api/deps.py`):
  - `require_admin_auth` — require an authenticated *admin user*.
  - `require_admin_or_agent` — allow either an admin user or an authenticated agent.
  - `get_board_for_actor_read` / `get_board_for_actor_write` — enforce board access for the calling actor.
  - `require_org_member` / `require_org_admin` — enforce org membership/admin for user callers.
- **Agent-only surface**: `backend/app/api/agent.py` uses `get_agent_auth_context` (X-Agent-Token) and contains board/task/memory endpoints specifically for automation.

### Module-by-module map (prefix, key endpoints, and pointers)

This is a “where to look” index, not a full OpenAPI dump. For exact parameters and response shapes, see:
- route module file (`backend/app/api/<module>.py`)
- schemas (`backend/app/schemas/*`)
- models (`backend/app/models/*`)
- services (`backend/app/services/*`)

| Module | Prefix (under `/api/v1`) | Key endpoints (examples) | Main deps / auth | Pointers (schemas/models/services) |
|---|---|---|---|---|
| `activity.py` | `/activity` | `GET /activity` (events); `GET /activity/task-comments` + `/stream` | `require_admin_or_agent`, `require_org_member` | `app/models/activity_events.py`, `app/schemas/activity_events.py` |
| `agent.py` | `/agent` | agent automation surface: boards/tasks/memory + gateway coordination | `get_agent_auth_context` (X-Agent-Token) | `backend/app/core/agent_auth.py`, `backend/app/services/openclaw/*` |
| `agents.py` | `/agents` | agent lifecycle + SSE stream + heartbeat | org-admin gated for user callers; some endpoints allow agent access via deps | `app/schemas/agents.py`, `app/services/openclaw/provisioning_db.py` |
| `approvals.py` | `/boards/{board_id}/approvals` | list/create/update approvals + `/stream` | `require_admin_or_agent` + board access deps | `app/models/approvals.py`, `app/schemas/approvals.py` |
| `auth.py` | `/auth` | `POST /auth/bootstrap` | `get_auth_context` (Clerk/user) | `backend/app/core/auth.py`, `app/schemas/users.py` |
| `board_group_memory.py` | `/board-groups/{group_id}/memory` and `/boards/{board_id}/group-memory` | list/create + `/stream` (group + board-context views) | `require_admin_or_agent`, `require_org_member`, board access deps | `app/models/board_group_memory.py`, `app/schemas/board_group_memory.py` |
| `board_groups.py` | `/board-groups` | CRUD + snapshot + heartbeat apply | `require_org_member` / `require_org_admin` | `app/services/board_group_snapshot.py` |
| `board_memory.py` | `/boards/{board_id}/memory` | list/create + `/stream` | `require_admin_or_agent` + board access deps | `app/models/board_memory.py`, `app/schemas/board_memory.py` |
| `board_onboarding.py` | `/boards/{board_id}/onboarding` | start/answer/confirm onboarding; agent update callback | mix of admin-user and admin-or-agent deps | `app/models/board_onboarding.py`, `app/services/openclaw/onboarding_service.py` |
| `boards.py` | `/boards` | list/create/update/delete; `/snapshot`; `/group-snapshot` | user/org access (`require_org_member`); read access via `get_board_for_actor_read` in some paths | `app/services/board_snapshot.py`, `app/schemas/boards.py` |
| `gateway.py` | `/gateways` | session inspection + supported commands list | org-admin user only | `backend/app/services/openclaw/gateway_rpc.py`, `app/schemas/gateway_api.py` |
| `gateways.py` | `/gateways` | gateway CRUD + template sync | org-admin user only | `app/models/gateways.py`, `app/services/openclaw/*` |
| `metrics.py` | `/metrics` | `GET /metrics/dashboard` | org-member user access | `app/schemas/metrics.py` |
| `organizations.py` | `/organizations` | org create + invites/membership flows | user (Clerk) + org member/admin checks | `app/services/organizations.py` |
| `souls_directory.py` | `/souls-directory` | search + fetch markdown entries | `require_admin_or_agent` | `app/services/souls_directory.py`, `app/schemas/souls_directory.py` |
| `tasks.py` | `/boards/{board_id}/tasks` | list/create/update/delete tasks; comments; `/stream` | mix of admin-only + admin-or-agent; board access via deps | `app/models/tasks.py`, `app/schemas/tasks.py`, `app/services/task_dependencies.py` |
| `users.py` | `/users` | `GET/PATCH/DELETE /users/me` | user (Clerk) | `app/models/users.py`, `app/schemas/users.py` |

## `/activity` — `activity.py`
*Activity listing and task-comment feed endpoints.*

### router (prefix `/activity`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/activity` | `list_activity()` | List activity events visible to the calling actor. |
| `GET` | `/api/v1/activity/task-comments` | `list_task_comment_feed()` | List task-comment feed items for accessible boards. |
| `GET` | `/api/v1/activity/task-comments/stream` | `stream_task_comment_feed()` | Stream task-comment events for accessible boards. |

## `/agent` — `agent.py`
*Agent-scoped API routes for board operations and gateway coordination.*

### Agent automation API (`/api/v1/agent/*`)

Auth:
- Header: `X-Agent-Token: <token>`
- See: `backend/app/core/agent_auth.py` and `backend/app/api/deps.py`

High-signal endpoint index (from `backend/app/api/agent.py`):

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/agent/heartbeat` | Agent check-in / heartbeat status |
| `GET` | `/api/v1/agent/boards` | List boards visible to the agent |
| `GET` | `/api/v1/agent/boards/{board_id}/tasks` | List tasks with filters (status, assignment, etc.) |
| `PATCH` | `/api/v1/agent/boards/{board_id}/tasks/{task_id}` | Update task fields (status/assignment/etc.) |
| `GET` | `/api/v1/agent/boards/{board_id}/tasks/{task_id}/comments` | List task comments |
| `POST` | `/api/v1/agent/boards/{board_id}/tasks/{task_id}/comments` | Create task comment (note: request body uses `message`) |
| `GET` | `/api/v1/agent/boards/{board_id}/memory` | List board memory entries |
| `POST` | `/api/v1/agent/boards/{board_id}/memory` | Create board memory entry |
| `POST` | `/api/v1/agent/boards/{board_id}/gateway/main/ask-user` | Route an “ask user” message through gateway-main |
| `POST` | `/api/v1/agent/gateway/leads/broadcast` | Broadcast a gateway-main message to multiple board leads |

### router (prefix `/agent`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/agent/agents` | `list_agents()` | List agents, optionally filtered to a board. |
| `POST` | `/api/v1/agent/agents` | `create_agent()` | Create an agent on the caller's board. |
| `GET` | `/api/v1/agent/boards` | `list_boards()` | List boards visible to the authenticated agent. |
| `POST` | `/api/v1/agent/heartbeat` | `agent_heartbeat()` | Record heartbeat status for the authenticated agent. |
| `GET` | `/api/v1/agent/boards/{board_id}` | `get_board()` | Return a board if the authenticated agent can access it. |
| `GET` | `/api/v1/agent/boards/{board_id}/tasks` | `list_tasks()` | List tasks on a board with optional status and assignment filters. |
| `POST` | `/api/v1/agent/boards/{board_id}/tasks` | `create_task()` | Create a task on the board as the lead agent. |
| `POST` | `/api/v1/agent/gateway/leads/broadcast` | `broadcast_gateway_lead_message()` | Broadcast a gateway-main message to multiple board leads. |
| `GET` | `/api/v1/agent/boards/{board_id}/memory` | `list_board_memory()` | List board memory entries with optional chat filtering. |
| `POST` | `/api/v1/agent/boards/{board_id}/memory` | `create_board_memory()` | Create a board memory entry. |

## `/agents` — `agents.py`
*Thin API wrappers for async agent lifecycle operations.*

### router (prefix `/agents`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/agents` | `list_agents()` | List agents visible to the active organization admin. |
| `POST` | `/api/v1/agents` | `create_agent()` | Create and provision an agent. |
| `GET` | `/api/v1/agents/stream` | `stream_agents()` | Stream agent updates as SSE events. |
| `POST` | `/api/v1/agents/heartbeat` | `heartbeat_or_create_agent()` | Heartbeat an existing agent or create/provision one if needed. |
| `DELETE` | `/api/v1/agents/{agent_id}` | `delete_agent()` | Delete an agent and clean related task state. |
| `GET` | `/api/v1/agents/{agent_id}` | `get_agent()` | Get a single agent by id. |
| `PATCH` | `/api/v1/agents/{agent_id}` | `update_agent()` | Update agent metadata and optionally reprovision. |
| `POST` | `/api/v1/agents/{agent_id}/heartbeat` | `heartbeat_agent()` | Record a heartbeat for a specific agent. |

## `/boards/{board_id}/approvals` — `approvals.py`
*Approval listing, streaming, creation, and update endpoints.*

### router (prefix `/boards/{board_id}/approvals`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards/{board_id}/approvals` | `list_approvals()` | List approvals for a board, optionally filtering by status. |
| `POST` | `/api/v1/boards/{board_id}/approvals` | `create_approval()` | Create an approval for a board. |
| `GET` | `/api/v1/boards/{board_id}/approvals/stream` | `stream_approvals()` | Stream approval updates for a board using server-sent events. |
| `PATCH` | `/api/v1/boards/{board_id}/approvals/{approval_id}` | `update_approval()` | Update an approval's status and resolution timestamp. |

## `/auth` — `auth.py`
*Authentication bootstrap endpoints for the Mission Control API.*

### router (prefix `/auth`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `POST` | `/api/v1/auth/bootstrap` | `bootstrap_user()` | Return the authenticated user profile from token claims. |

## `` — `board_group_memory.py`
*Board-group memory CRUD and streaming endpoints.*

### board_router (prefix `/boards/{board_id}/group-memory`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards/{board_id}/group-memory` | `list_board_group_memory_for_board()` | List memory entries for the board's linked group. |
| `POST` | `/api/v1/boards/{board_id}/group-memory` | `create_board_group_memory_for_board()` | Create a group memory entry from a board context and notify recipients. |
| `GET` | `/api/v1/boards/{board_id}/group-memory/stream` | `stream_board_group_memory_for_board()` | Stream memory entries for the board's linked group. |

### group_router (prefix `/board-groups/{group_id}/memory`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/board-groups/{group_id}/memory` | `list_board_group_memory()` | List board-group memory entries for a specific group. |
| `POST` | `/api/v1/board-groups/{group_id}/memory` | `create_board_group_memory()` | Create a board-group memory entry and notify chat recipients. |
| `GET` | `/api/v1/board-groups/{group_id}/memory/stream` | `stream_board_group_memory()` | Stream memory entries for a board group via server-sent events. |

## `/board-groups` — `board_groups.py`
*Board group CRUD, snapshot, and heartbeat endpoints.*

### router (prefix `/board-groups`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/board-groups` | `list_board_groups()` | List board groups in the active organization. |
| `POST` | `/api/v1/board-groups` | `create_board_group()` | Create a board group in the active organization. |
| `DELETE` | `/api/v1/board-groups/{group_id}` | `delete_board_group()` | Delete a board group. |
| `GET` | `/api/v1/board-groups/{group_id}` | `get_board_group()` | Get a board group by id. |
| `PATCH` | `/api/v1/board-groups/{group_id}` | `update_board_group()` | Update a board group. |
| `GET` | `/api/v1/board-groups/{group_id}/snapshot` | `get_board_group_snapshot()` | Get a snapshot across boards in a group. |
| `POST` | `/api/v1/board-groups/{group_id}/heartbeat` | `apply_board_group_heartbeat()` | Apply heartbeat settings to agents in a board group. |

## `/boards/{board_id}/memory` — `board_memory.py`
*Board memory CRUD and streaming endpoints.*

### router (prefix `/boards/{board_id}/memory`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards/{board_id}/memory` | `list_board_memory()` | List board memory entries, optionally filtering chat entries. |
| `POST` | `/api/v1/boards/{board_id}/memory` | `create_board_memory()` | Create a board memory entry and notify chat targets when needed. |
| `GET` | `/api/v1/boards/{board_id}/memory/stream` | `stream_board_memory()` | Stream board memory events over server-sent events. |

## `/boards/{board_id}/onboarding` — `board_onboarding.py`
*Board onboarding endpoints for user/agent collaboration.*

### router (prefix `/boards/{board_id}/onboarding`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards/{board_id}/onboarding` | `get_onboarding()` | Get the latest onboarding session for a board. |
| `POST` | `/api/v1/boards/{board_id}/onboarding/agent` | `agent_onboarding_update()` | Store onboarding updates submitted by the gateway agent. |
| `POST` | `/api/v1/boards/{board_id}/onboarding/start` | `start_onboarding()` | Start onboarding and send instructions to the gateway agent. |
| `POST` | `/api/v1/boards/{board_id}/onboarding/answer` | `answer_onboarding()` | Send a user onboarding answer to the gateway agent. |
| `POST` | `/api/v1/boards/{board_id}/onboarding/confirm` | `confirm_onboarding()` | Confirm onboarding results and provision the board lead agent. |

## `/boards` — `boards.py`
*Board CRUD and snapshot endpoints.*

### router (prefix `/boards`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards` | `list_boards()` | List boards visible to the current organization member. |
| `POST` | `/api/v1/boards` | `create_board()` | Create a board in the active organization. |
| `DELETE` | `/api/v1/boards/{board_id}` | `delete_board()` | Delete a board and all dependent records. |
| `GET` | `/api/v1/boards/{board_id}` | `get_board()` | Get a board by id. |
| `PATCH` | `/api/v1/boards/{board_id}` | `update_board()` | Update mutable board properties. |
| `GET` | `/api/v1/boards/{board_id}/snapshot` | `get_board_snapshot()` | Get a board snapshot view model. |
| `GET` | `/api/v1/boards/{board_id}/group-snapshot` | `get_board_group_snapshot()` | Get a grouped snapshot across related boards. |

## `/gateways` — `gateway.py`
*Thin gateway session-inspection API wrappers.*

### router (prefix `/gateways`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/gateways/status` | `gateways_status()` | Return gateway connectivity and session status. |
| `GET` | `/api/v1/gateways/commands` | `gateway_commands()` | Return supported gateway protocol methods and events. |
| `GET` | `/api/v1/gateways/sessions` | `list_gateway_sessions()` | List sessions for a gateway associated with a board. |
| `GET` | `/api/v1/gateways/sessions/{session_id}` | `get_gateway_session()` | Get a specific gateway session by key. |
| `GET` | `/api/v1/gateways/sessions/{session_id}/history` | `get_session_history()` | Fetch chat history for a gateway session. |
| `POST` | `/api/v1/gateways/sessions/{session_id}/message` | `send_gateway_session_message()` | Send a message into a specific gateway session. |

## `/gateways` — `gateways.py`
*Thin API wrappers for gateway CRUD and template synchronization.*

### router (prefix `/gateways`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/gateways` | `list_gateways()` | List gateways for the caller's organization. |
| `POST` | `/api/v1/gateways` | `create_gateway()` | Create a gateway and provision or refresh its main agent. |
| `DELETE` | `/api/v1/gateways/{gateway_id}` | `delete_gateway()` | Delete a gateway in the caller's organization. |
| `GET` | `/api/v1/gateways/{gateway_id}` | `get_gateway()` | Return one gateway by id for the caller's organization. |
| `PATCH` | `/api/v1/gateways/{gateway_id}` | `update_gateway()` | Patch a gateway and refresh the main-agent provisioning state. |
| `POST` | `/api/v1/gateways/{gateway_id}/templates/sync` | `sync_gateway_templates()` | Sync templates for a gateway and optionally rotate runtime settings. |

## `/metrics` — `metrics.py`
*Dashboard metric aggregation endpoints.*

### router (prefix `/metrics`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/metrics/dashboard` | `dashboard_metrics()` | Return dashboard KPIs and time-series data for accessible boards. |

## `/organizations` — `organizations.py`
*Organization management endpoints and membership/invite flows.*

### router (prefix `/organizations`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `POST` | `/api/v1/organizations` | `create_organization()` | Create an organization and assign the caller as owner. |
| `DELETE` | `/api/v1/organizations/me` | `delete_my_org()` | Delete the active organization and related entities. |
| `GET` | `/api/v1/organizations/me` | `get_my_org()` | Return the caller's active organization. |
| `GET` | `/api/v1/organizations/me/list` | `list_my_organizations()` | List organizations where the current user is a member. |
| `PATCH` | `/api/v1/organizations/me/active` | `set_active_org()` | Set the caller's active organization. |
| `GET` | `/api/v1/organizations/me/member` | `get_my_membership()` | Get the caller's membership record in the active organization. |
| `GET` | `/api/v1/organizations/me/invites` | `list_org_invites()` | List pending invites for the active organization. |
| `POST` | `/api/v1/organizations/me/invites` | `create_org_invite()` | Create an organization invite for an email address. |
| `GET` | `/api/v1/organizations/me/members` | `list_org_members()` | List members for the active organization. |
| `POST` | `/api/v1/organizations/invites/accept` | `accept_org_invite()` | Accept an invite and return resulting membership. |

## `/souls-directory` — `souls_directory.py`
*API routes for searching and fetching souls-directory markdown entries.*

### router (prefix `/souls-directory`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/souls-directory/search` | `search()` | Search souls-directory entries by handle/slug query text. |
| `GET` | `/api/v1/souls-directory/{handle}/{slug}` | `get_markdown()` | Fetch markdown content for a validated souls-directory handle and slug. |
| `GET` | `/api/v1/souls-directory/{handle}/{slug}.md` | `get_markdown()` | Fetch markdown content for a validated souls-directory handle and slug. |

## `/boards/{board_id}/tasks` — `tasks.py`
*Task API routes for listing, streaming, and mutating board tasks.*

### router (prefix `/boards/{board_id}/tasks`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `GET` | `/api/v1/boards/{board_id}/tasks` | `list_tasks()` | List board tasks with optional status and assignment filters. |
| `POST` | `/api/v1/boards/{board_id}/tasks` | `create_task()` | Create a task and initialize dependency rows. |
| `GET` | `/api/v1/boards/{board_id}/tasks/stream` | `stream_tasks()` | Stream task and task-comment events as SSE payloads. |
| `DELETE` | `/api/v1/boards/{board_id}/tasks/{task_id}` | `delete_task()` | Delete a task and related records. |
| `PATCH` | `/api/v1/boards/{board_id}/tasks/{task_id}` | `update_task()` | Update task status, assignment, comment, and dependency state. |
| `GET` | `/api/v1/boards/{board_id}/tasks/{task_id}/comments` | `list_task_comments()` | List comments for a task in chronological order. |
| `POST` | `/api/v1/boards/{board_id}/tasks/{task_id}/comments` | `create_task_comment()` | Create a task comment and notify relevant agents. |

## `/users` — `users.py`
*User self-service API endpoints for profile retrieval and updates.*

### router (prefix `/users`)

| Method | Path | Handler | Notes |
|---|---|---|---|
| `DELETE` | `/api/v1/users/me` | `delete_me()` | Delete the authenticated account and any personal-only organizations. |
| `GET` | `/api/v1/users/me` | `get_me()` | Return the authenticated user's current profile payload. |
| `PATCH` | `/api/v1/users/me` | `update_me()` | Apply partial profile updates for the authenticated user. |
