---
name: "context-rot-prevention"
description: "Detect a session that is outgrowing its context window and hand the work to a fresh, nested context before it degrades. Use when a session runs long, shows cumulative weight (many turns, many files edited, re-reading state), the context window feels full or close to it, or the user asks to continue elsewhere / spin up a new session / avoid losing the thread."
---

# Context Rot Prevention

Prevents context rot: hands a session that has grown heavy off to a fresh, nested context (auto-spawn when the tool allows it, otherwise a self-contained handoff prompt) before output quality drops. Full procedure, rationale, and the handoff template live in [`docs/context-rot.md`](../../docs/context-rot.md).

## When to use
- A session has many turns, many distinct files read or edited, or keeps re-reading files it already loaded.
- You catch yourself re-deriving state you already settled earlier in the conversation.
- Token-usage telemetry (where the tool exposes it) shows the context window is near the cap.
- The user asks to split, continue in a fresh session, or hand the thread off.
- A slice of work is done and the next slice is better done with a clean context.

## Don't use for
- **Short or one-shot tasks** that will finish in the current context. Splitting is overhead.
- **Near-complete work.** A handoff costs more than seeing it through.
- **Parallel fan-out of subtasks into many agents.** That is `workflow-orchestration.md` / the Workflow tool, not a continuity handoff.

## Decision
1. **Assess the envelope.** Weight the cumulative signals (turns, working-set size, re-deriving state, telemetry if present). No single number decides; read the shape.
2. **Checkpoint.** Commit or otherwise leave the tree in a known state; write a memory note for non-obvious decisions.
3. **Split: use a native nested-session primitive when available and safe.** This Copilot app: `create_session` / `send_session_message`. Claude Code: `claude --continue` or a typed subagent. Codex: `codex resume`. Cross-CLI read-only fan-out: `agent orchestrator`.
4. **Else: emit a self-contained handoff prompt.** Write it so a fresh session with zero prior context can continue immediately, and tell the user where it goes. Use the template in the doc.

The handoff prompt must carry: goal, done-so-far, current state (branch, HEAD, key files), decisions already made, exact next step, and where to re-derive context.

## Example
A session has dug through 30 files wiring `CancelContract`, the agent is re-opening files it already read, and the work is mid-flight. The agent checkpoints (commit + memory note), then emits a handoff prompt capturing goal, done-so-far, current state, settled decisions (soft-cancel, 202/409 semantics), and the exact next step (add the idempotency guard). The user pastes it into a fresh session and work continues with a lean context.