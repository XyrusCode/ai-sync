# AGENTS — Global instructions and critical rules

## Critical Rules

- Prevent context rot: When a session grows heavy (many turns, many files, re-deriving state), split the work into a fresh, nested context before output quality degrades. Use a native nested-session primitive if available; otherwise emit a self-contained handoff prompt. Checkpoint before splitting. See `docs/context-rot.md` for full procedure and templates.

- Never commit directly to main. Always create a branch and open a Pull Request for review and CI before merging. This repository enforces review-first changes.

(Other global rules and conventions live here.)
