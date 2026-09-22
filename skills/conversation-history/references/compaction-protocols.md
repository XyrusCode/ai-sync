# Compaction Protocols

This document defines concrete heuristics and formats for condensing tool outputs, compacting conversation turns, and controlling token consumption.

## Tool Output Condensation

Raw tool outputs are the primary source of context bloat. Never paste or leave full diagnostic streams in the conversation narrative without summarizing them.

### 1. Test Suite Results
- **Bad**: Pasting 120 lines of pytest or vitest output showing every passing test name and environment header.
- **Good**: "Ran 64 tests: 63 passed, 1 failed. Failure: `test_token_refresh` in `tests/test_auth.py:42` (expected status 200, got 401 due to expired test fixture)."

### 2. Compiler and Build Logs
- **Bad**: Retaining 80 lines of TypeScript compiler stack traces.
- **Good**: "Build failed with TS2322 in `src/services/api.ts:18`: Type 'null' is not assignable to type 'string'. Fixed by adding optional chaining."

### 3. File Searches and Directory Listings
- **Bad**: Pasting the entire output of `find` or `list_dir` containing 150 irrelevant paths.
- **Good**: "Searched for storage adapters: found 3 relevant files (`s3.py`, `local.py`, `gcs.py`). Focusing on `local.py`."

### 4. Git Diffs and Status
- **Bad**: Re-printing full diffs across 10 modified files.
- **Good**: "Staged 3 files (`User.php`, `UserController.php`, `UserTest.php`). Added password reset rate limit guard."

## Rolling State Checkpoints

When an agent completes a coherent subtask or reaches 15 to 20 turns, synthesize the progress into a Rolling State Checkpoint.

### Checkpoint Anatomy
A rolling checkpoint distills the preceding turns into four components:
1. **Settled State**: What is confirmed working and verified on disk.
2. **Key Findings**: Crucial discoveries made during investigation.
3. **Discarded Paths**: Dead ends or disproven hypotheses, recorded so they are not repeated.
4. **Immediate Vector**: The next exact command or edit.

Once a checkpoint is emitted, the agent can treat all earlier debugging chatter as superseded.

## Trigger Envelope for Session Handoff

When a conversation exceeds manageable weight, split the thread instead of trying to force it further.

Signals to split:
- **Turn count**: 40 or more substantive turns.
- **File churn**: More than 15 distinct files opened, edited, or inspected.
- **Re-deriving state**: The agent starts re-reading configs or asking questions answered earlier in the thread.
- **Model degradation**: Responses become repetitive, forget settled decisions, or truncate prematurely.

When these signals appear, emit the clean handoff prompt ([templates/session-handoff.md](../templates/session-handoff.md)) following `docs/context-rot.md`.
