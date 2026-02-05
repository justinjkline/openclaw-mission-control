# AGENTS.md

This workspace is your home. Treat it as the source of truth.

## First run
- If BOOTSTRAP.md exists, follow it once and delete it when finished.

## Every session
Before doing anything else:
1) Read SOUL.md (identity, boundaries)
2) Read USER.md (who you serve)
3) Read memory/YYYY-MM-DD.md for today and yesterday (create memory/ if missing)
4) If this is the main or direct session, also read memory.md

## Memory
- Daily log: memory/YYYY-MM-DD.md
- Long-term: memory.md (main session only)

Write things down. Do not rely on short-term context.

## Safety
- Ask before destructive actions.
- Prefer reversible steps.
- Do not exfiltrate private data.

## Tools
- Skills are authoritative. Follow SKILL.md instructions exactly.
- Use TOOLS.md for environment-specific notes.

## Heartbeats
- HEARTBEAT.md defines what to do on each heartbeat.
- Lead agents receive a lead-specific HEARTBEAT.md. Follow it exactly.

## Task updates
- All task updates MUST be posted to the task comments endpoint.
- Do not post task updates in chat/web channels under any circumstance.
- You may include comments directly in task PATCH requests using the `comment` field.
- Required comment fields (markdown):
  - `status`: inbox | in_progress | review | done
  - `summary`: one line
  - `details`: 1–3 bullets
  - `next`: next step or handoff request
- Comments must be markdown content (no plain‑text status updates).
- Every status change must include a comment within 30 seconds (see HEARTBEAT.md).
