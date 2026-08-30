---
name: feedback_context_rot_prevention
description: "Prevent context rot: when a session outgrows its context window (many turns, many files, re-deriving state), split the work into a fresh, nested context before it degrades. Use a native spawn primitive if available; else emit a self-contained handoff prompt. Checkpoint before splitting."
metadata:
  node_type: memory
  type: feedback
---

Enforced machine-wide so every agent hands saturated work off instead of soldiering on to rot.

**Detection is a heuristic envelope, not a hard threshold.** Split on cumulative weight: ~40+ heavy turns, a large working-set of distinct files, or the agent re-reading files/settled context to re-derive its own state (strongest signal). Token telemetry where a tool exposes it boosts the heuristic; absence does not block a split.

**Split action is hybrid.** Prefer nested session primitives (create_session / send_session_message, or tool-specific resume/continue commands). Otherwise emit a self-contained handoff prompt (goal, done-so-far, current state, decisions, exact next step, where to re-derive context). Checkpoint (commit or leave known tree state + memory note) before splitting.
