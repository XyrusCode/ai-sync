# Project Decision Log (CONVERSATION_HISTORY.md)

The project decision log is a committed, markdown record maintained in the project repository (commonly at `docs/CONVERSATION_HISTORY.md` or `CONVERSATION_HISTORY.md`).

It serves as the durable chronological source of truth across sessions, agents, and days. Instead of relying on volatile, multi-thousand token chat transcripts, agents append a concise entry to this log whenever a session finishes or reaches an inflection point.

## Why This Works

1. **Zero-token-waste rehydration**: When starting a fresh session or recovering from an interruption, reading the decision log re-establishes the complete project context in under 1,500 tokens.
2. **Irreversible scope boundaries**: Captures explicit trade-offs, deferred features, and accepted constraints so subsequent sessions never re-open settled debates.
3. **Accountability and proof**: Records exact root causes, bug fixes, files touched, and test verification metrics.

## Entry Structure

Each entry in `CONVERSATION_HISTORY.md` follows this standard format:

```markdown
## YYYY-MM-DD: [Descriptive Topic Title]

- **User Intent**: The problem, request, or business goal stated by the user.
- **Scope Decisions**:
  - Accepted into current scope, with rationale.
  - Explicitly deferred to future phases, preventing scope creep.
- **Architectural Choices and Shortcuts**:
  - Key technical patterns selected.
  - Any explicit shortcut accepted for speed, including its ceiling and upgrade trigger.
- **Implementation Details**:
  - Exact files created or modified (models, controllers, views, configs, migrations).
  - Routes, database tables, or contracts introduced.
- **Diagnostics and Root Cause** (for bug fixes):
  - Error message and failure mechanism.
  - The exact code change that resolved it.
- **Verification and Test Results**:
  - Test suites executed and pass rates (for example, "98/98 tests passing, 100% green, 372 assertions").
  - Build outcomes, asset compilation times, or manual flow verifications.
```

## Lifecycle and Workflow

1. **Session Start**:
   - Check if `CONVERSATION_HISTORY.md` exists in the repository.
   - Read the latest 2 or 3 entries to understand recent decisions and current momentum.
   - Initialize the intra-session Active Objectives Ledger based on the log's state.

2. **Mid-Session / Interruption**:
   - If a review or session is interrupted (for example, reaching token or rate limits), record the exact resume point and open choices in a temporary checkpoint (like `CEO_INTERRUPTED.md`) and note it in the log.

3. **Session Wind Down**:
   - Before ending the session, compose a new chronological entry using `templates/conversation-history-entry.md`.
   - Append it to `CONVERSATION_HISTORY.md`.
   - Commit the updated log alongside the code changes.
