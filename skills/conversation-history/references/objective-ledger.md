# Active Objectives Ledger

The Active Objectives Ledger is a structured working state block kept in the conversation. Its purpose is to anchor the agent to the core task, preventing drift when execution requires deep diagnostic loops, multiple tool calls, or exploratory steps.

## Principles

1. **Keep it small**: The ledger should stay between 10 and 20 lines. A bloated ledger defeats its own purpose of token reduction.
2. **Update in-place**: Overwrite or replace the ledger state as steps finish. Do not append new ledger copies turn after turn.
3. **Lock settled decisions**: Once an approach or constraint is decided, record it under locked decisions. Never allow subsequent turns to re-litigate settled choices unless new technical evidence invalidates them.
4. **Surface blockers clearly**: If a step cannot proceed, name the exact file, error, or missing requirement.

## Ledger Sections

### Goal
The top-level objective requested by the user. State it in one or two plain sentences with verifiable success criteria.

### Active Phase
The exact step in progress right now. There must be only one active phase at any moment.

### Completed Milestones
Bullet list of finished items. Each line should be short and confirm verification (for example, "Config parser tests passing").

### Locked Decisions
Technical choices, invariants, and constraints agreed upon with the user or determined by code architecture.
Examples:
- "Use native SQLite rather than adding an external ORM dependency."
- "HTTP 409 returned for duplicate submissions."

### Open Questions and Blockers
Items requiring clarification or blocking progress. When empty, state "None".

## Lifecycle

```
[Start of task]
      │
      ▼
Initialize Ledger (Goal + Planned Phases)
      │
      ▼
Execute Active Phase (Run tools, edit code, run tests)
      │
      ▼
Phase Completed?
 ├── Yes ──> Move item to Completed Milestones
 │           Record new Locked Decisions
 │           Advance Active Phase
 └── No  ──> Record Blocker if stuck; resolve before moving on
      │
      ▼
Periodic Refresh (Every 10-15 turns or after noisy tool runs)
```

## Example

```markdown
### Active Objectives Ledger
- **Goal**: Implement token-budget compaction for conversation transcripts in ai-sync.
- **Active Phase**: Writing test cases for turn pruner in tests/test_compaction.py.
- **Completed Milestones**:
  - Defined CompactionProfile dataclass in ai_sync/compaction.py.
  - Implemented raw log condenser for pytest and git diffs.
- **Locked Decisions**:
  - Keep compaction deterministic: use AST and regex heuristics, no LLM call required.
  - Retain the most recent 3 turns uncompressed.
- **Blockers**: None.
```
