# Context Rot Prevention

How to spot a session that is outgrowing its context window and hand the work to a fresh, nested context before it degrades. Load this doc when a session shows cumulative weight; the always-on rule is in `AGENTS.md`, and the trigger skill is `context-rot-prevention`.

## The problem

Every agent session has a finite context window. As a session grows long it starts re-deriving state it already loaded, re-reading files and tool outputs to re-establish what it once knew, and losing track of earlier decisions. That is context rot: output quality drops, scope drifts, and the agent burns tokens re-loading context instead of doing work.

The fix is not to make the window bigger. It is to split work across fresh contexts at natural points, where each new context starts lean and fully rehydrated.

## Detection: the heuristic envelope

There is no reliable, tool‑agnostic "you are at 85% of the window" signal, because most agents do not expose live token usage. Decide to split on cumulative weight, not a single hard threshold. Any of these is a signal:

- Turns or request volume. A session has grown heavy (roughly 40+ substantive turns), or the same conversation keeps returning to earlier material.
- Working-set size. Many distinct files have been read or edited; the live working set no longer fits comfortably.
- Re-deriving state. The agent is re-reading files, configs, or its own earlier output to remember what it already settled. This is the strongest signal.
- Token telemetry where available. When a tool exposes context-usage figures, treat them as a strong boost. Absence of telemetry never blocks a split; the weight signals above are enough.

There is no single number that decides. Read the envelope: a 3-file-focused task across 60 turns may be fine; a 20-file sweep across 15 turns may not.

## The split action: hybrid

When a split is warranted, do the cheapest thing that keeps the work in a fresh context:

1. Use a native nested-session primitive when it is available and safe. Prefer it; it is automatic and keeps the handoff inside the toolchain (examples: this Copilot app `create_session` / `send_session_message`; Claude Code `claude --continue` or a typed subagent; Codex `codex resume`; cross-CLI read-only fan-out via `agent orchestrator`).

2. Else, emit a self-contained handoff prompt. Write a prompt the user (or the app) can paste into a brand-new session with no other context. Emitting a handoff prompt always works, on every agent, with zero infrastructure. When you hand the prompt to the user, say what it is and where it goes.

The split is not a fan-out of subtasks into parallel agents (that is `workflow-orchestration.md`). This is a continuity handoff: one piece of work carries on in a fresh context.

## Checkpoint before you split

Never split mid-mutation. Before handoff:

1. Make current work durable. Commit, or at least leave the tree in a known state. Write a memory note capturing decisions if they are not already somewhere the fresh session will see them (`agent memory` / `~/.agents/memory`).
2. Give the fresh context everything it needs to rehydrate. Branch, commit/HEAD, the exact files touched, and the key decisions. The handoff prompt is what carries this; do not make the next session rediscover it.

## A handoff prompt must contain

Write the handoff prompt so a fresh session with zero prior context can continue immediately. Cover:

1. Goal. What this slice of work is trying to achieve, in one or two lines.
2. Done so far. What is finished. Concrete, file-level.
3. Current state. Branch, HEAD/commit, and the files that matter. Give paths.
4. Key decisions and constraints. Non-negotiables already settled, so the next context does not re-litigate them.
5. Exact next step. The single next action to take. This is what unblocks momentum.
6. How to re-derive context. Where to look (docs, memory note, README) to reconstruct anything not stated.

And a "don't" section: what is out of scope for this child context, so it stays lean.

### Handoff template

```
Goal:
  <one-two line goal for this split>

Done so far:
  - <what is already done, file-level>

Current state:
  - Branch: <branch>  HEAD: <short-commit>
  - Key files: <paths, one per line>
  - Any running processes / servers / ports

Decisions already made (do not re-litigate):
  - <decision>

Next step:
  <the single next action to take>

How to re-derive context from:
  - <memory note name or path>
  - <doc or file that explains the project shape>

Out of scope for this context:
  - <what to defer>
```

## Example

Goal: Finish the CancelContract flow so cancellation is idempotent and audit-logged.

Done so far:
  - Added CancelContract request + validation in app/Contracts/Requests.
  - Wired the controller action to the service; POST /contracts/{id}/cancel returns 202.
  - Tests in tests/Feature/ContractCancellationTest cover happy path and duplicate cancel.

Current state:
  - Branch: feature/cancel-contract  HEAD: 4a8cf23
  - Key files:
    - app/Contracts/Http/Controllers/ContractController.php
    - app/Contracts/Services/CancelContractService.php

Next step:
  Add the idempotency guard (request id lookup) in CancelContractService before the status transition; then the existing duplicate-cancel test should pass.

User pastes the handoff prompt into a fresh session and work continues with a lean context.
