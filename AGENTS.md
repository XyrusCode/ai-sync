# AGENTS — Global instructions and critical rules

## Critical Rules

- Prevent context rot: When a session grows heavy (many turns, many files, re-deriving state), split the work into a fresh, nested context before output quality degrades. Use a native nested-session primitive if available; otherwise emit a self-contained handoff prompt. Checkpoint before splitting. See `docs/context-rot.md` for full procedure and templates.

(Other global rules and conventions live here.)
